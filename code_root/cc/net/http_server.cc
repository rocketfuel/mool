/*Implementation of http server module.*/
// Enable for miscellaneous logging.
// #define CC_TRACE_ENABLED
// Enable for API events (in both directions).
// #define TRACE_API_EVENTS
#include "cc/net/http_server.h"

#include "cc/net/assigned_pool.h"
#include "cc/net/epoll_server.h"
#include "cc/shared/refcounted_lookup.h"
#include "cc/shared/string_builder.h"
#include "cc/shared/timer_queue.h"

#include <boost/atomic.hpp>
#include <boost/lexical_cast.hpp>

using cc_shared::Mutex;
using cc_shared::NewCallback;
using cc_shared::RefcountedLookup;
using cc_shared::ScopedMutex;
using cc_shared::TimerCallbackContext;
using cc_shared::TimerQueue;
using cc_shared::scoped_ptr;
using std::map;
using std::string;
using std::vector;

namespace cc_net {

// TODO: Make this value a constructor parameter.
static const int kTimeoutThreadCount = 5;

class InnerHttpServer {
 public:
  InnerHttpServer(const char* host, const char* port, int worker_thread_count,
                  int max_latency_millis,
                  HttpRequestProcessor* timeout_processor)
      : epoll_server_(NULL), getter_(this),
        host_(host), port_(port), actual_port_(""), url_(""),
        worker_thread_count_(worker_thread_count),
        max_latency_millis_(max_latency_millis),
        timeout_processor_(timeout_processor),
        timer_queue_(timer_callback, kTimeoutThreadCount), running_(false),
        stopped_(true), timeout_count_(0), processed_count_(0),
        checked_out_count_(0), total_count_(0) {
    CHECK_EQ(NULL, epoll_server_.get());
    epoll_server_.replace(
        new(std::nothrow) EpollServer(host_.c_str(), port_.c_str(),
                                      &getter_, worker_thread_count_));
    actual_port_ = boost::lexical_cast<string>(
        epoll_server_->get_actual_port());
    url_ = "http://" + host_ + ":" + actual_port_;
    running_ = true;
    stopped_ = false;
  }

  ~InnerHttpServer() {
    stop();
  }

  const char* get_url() {
    return url_.c_str();
  }

  const char* get_actual_port() {
    return actual_port_.c_str();
  }

  void run() {
    static const int kSleepMicros = 50000;
    int iters = 0;
    while (running_) {
      usleep(kSleepMicros);
      ++iters;
      if (iters == 100) {
        if (getenv("DEBUG_OUT")) {
          std::cout << "Processed = "
                    << percentage_text(processed_count_, total_count_) << " "
                    << " Timed out = "
                    << percentage_text(timeout_count_, total_count_) << " "
                    << " Pulled = "
                    << percentage_text(checked_out_count_, total_count_)
                    << " Total = " << total_count_
                    << std::endl;
        }
        iters = 0;
      }
    }
    stop();
  }

  void cancel() {
    running_ = false;
  }

  void stop() {
    if (!stopped_) {
      TRACE_FILE_EVENT("Shutting down http server.");
      // Mark as not running. This will cause add_ready to ignore incoming
      // requests.
      running_ = false;

      // Stop the timer queue. This will fire timers for all existing requests.
      timer_queue_.stop();

      // Cleanup.
      ready_lookup_.clean_all_contexts();
      epoll_server_.reset();
      TRACE_FILE_EVENT("Shutdown complete.");
      stopped_ = true;
    }
    CHECK(!running_);
    CHECK(stopped_);
  }

  void set_max_latency_millis(int max_latency_millis) {
    max_latency_millis_ = max_latency_millis;
  }

  void checkout(HttpRequestProcessor* request_processor) {
    int64 current_id = -1;
    bool found = assigned_pool_.get_candidate(&current_id);
    if (!found) {
      return;
    }
    ++checked_out_count_;
    TRACE_API_EVENT("checkout for lookup_id " << current_id);
    (void) apply_processor(current_id, request_processor);
  }

  bool re_process(int64 id, HttpRequestProcessor* request_processor) {
    TRACE_API_EVENT("re_process for lookup_id " << id << " using "
                    << ((request_processor == timeout_processor_) ?
                        "timeout processor" : "specific processor"));
    return apply_processor(id, request_processor);
  }

 private:
  class ResponseContext {
   public:
    ResponseContext(HttpParser* parser,
                    HttpRequestProcessor* timeout_processor,
                    int64 connection_handle,
                    EpollServer* epoll_server,
                    InnerHttpServer* inner_http_server)
        : parser_(parser), timeout_processor_(timeout_processor),
          connection_handle_(connection_handle), epoll_server_(epoll_server),
          inner_http_server_(inner_http_server), committed_(false),
          instance_id_(-1) {
    }

    void set_instance_id(int64 instance_id) {
      ScopedMutex scoped(&lock_);
      instance_id_ = instance_id;
    }

    bool apply_processor(HttpRequestProcessor* processor) {
      ScopedMutex scoped(&lock_);
      if (committed_) {
        return false;
      }
      HttpRequestInstance request_instance(
          epoll_server_, connection_handle_, parser_.get(), instance_id_,
          committed_);
      TRACE_API_EVENT(__FUNCTION__ << " for lookup_id " << instance_id_
                      << " using "
                      << ((processor == timeout_processor_) ?
                           "timeout processor" : "specific processor"));
      processor->process(&request_instance);
      committed_ = request_instance.get_committed();
      if (committed_) {
        if (processor == timeout_processor_) {
          ++(inner_http_server_->timeout_count_);
        } else {
          ++(inner_http_server_->processed_count_);
        }
      }
      return committed_;
    }

    void finalize() {
      if (!committed_) {
        TRACE_API_EVENT(__FUNCTION__ << " for lookup_id " << instance_id_);
        apply_processor(timeout_processor_);
      }
      CHECK(committed_);
      delete this;
    }

   private:
    Mutex lock_;
    scoped_ptr<HttpParser> parser_;
    HttpRequestProcessor* timeout_processor_;
    int64 connection_handle_;
    EpollServer* epoll_server_;
    InnerHttpServer* inner_http_server_;
    bool committed_;
    int64 instance_id_;

    ~ResponseContext() {
    }

    DISALLOW_COPY_AND_ASSIGN(ResponseContext);
  };

  class ConnectionHandler : public EpollServer::EpollConnectionHandler {
   public:
    ConnectionHandler()
        : epoll_server_(NULL), connection_handle_(-1), inner_http_server_(NULL),
          parser_(NULL) {
    }

    virtual ~ConnectionHandler() {
    }

    void set_parent(InnerHttpServer* http_server) {
      inner_http_server_ = http_server;
    }

    virtual void set_context(int64 connection_handle,
                             EpollServer* epoll_server) {
      epoll_server_ = epoll_server;
      connection_handle_ = connection_handle;
    }

    virtual void handle_buffer(const char* buffer, int byte_count)  {
      // TODO: Add mechanism here to force disconnect peer if latencies become
      // too big.
      CHECK_LT(0, byte_count);
      TRACE_FILE_EVENT("Received " << byte_count << " bytes for "
                       << connection_handle_);

      if (!parser_.get()) {
        parser_.replace(new(std::nothrow) HttpParser());
        parser_->set_parse_request();
        parser_->setup();
      }
      CHECK(!(parser_->get_completed()));
      parser_->execute(buffer, byte_count);

      if (!(parser_->is_ok())) {
        TRACE_FILE_EVENT(
            "Closing connection after receiving malformed packet.");
        epoll_server_->close_connection(connection_handle_);
        return;
      }

      if (parser_->get_completed()) {
        ResponseContext* response_context =
            new(std::nothrow) ResponseContext(
                parser_.get(), inner_http_server_->timeout_processor_,
                connection_handle_, epoll_server_, inner_http_server_);
        parser_.replace(NULL);
        inner_http_server_->add_ready(response_context);
      }
    }

   private:
    EpollServer* epoll_server_;
    int64 connection_handle_;
    InnerHttpServer* inner_http_server_;
    scoped_ptr<HttpParser> parser_;
    DISALLOW_COPY_AND_ASSIGN(ConnectionHandler);
  };

 private:
  friend class ConnectionHandler;
  scoped_ptr<EpollServer> epoll_server_;
  HandlerGetter<InnerHttpServer, ConnectionHandler> getter_;
  string host_;
  string port_;
  string actual_port_;
  string url_;
  int worker_thread_count_;
  int max_latency_millis_;
  HttpRequestProcessor* timeout_processor_;
  TimerQueue timer_queue_;

  boost::atomic<bool> running_;
  boost::atomic<bool> stopped_;

  AssignedPool assigned_pool_;
  RefcountedLookup ready_lookup_;

  boost::atomic<int64> timeout_count_;
  boost::atomic<int64> processed_count_;
  boost::atomic<int64> checked_out_count_;
  boost::atomic<int64> total_count_;

  void add_ready(ResponseContext* response_context) {
    ++total_count_;
    if ((!running_) || (max_latency_millis_ <= 0)) {
      response_context->finalize();
      return;
    }
    // Create new lookup id.
    int64 lookup_id = ready_lookup_.get_new_id(
        response_context, NewCallback(response_context,
                                      &ResponseContext::finalize));
    response_context->set_instance_id(lookup_id);
    TRACE_API_EVENT("add_ready for lookup_id " << lookup_id);

    // Setup timer callback.
    TimerCallbackContext context;
    context.value1 = reinterpret_cast<int64>(this);
    context.value2 = lookup_id;
    timer_queue_.add_item(context,
                          get_epoch_milliseconds() + max_latency_millis_);
    assigned_pool_.insert(lookup_id);
  }

  void send_timeout_response(int64 lookup_id) {
    TRACE_API_EVENT("send_timeout_response for lookup_id " << lookup_id);
    (void) apply_processor(lookup_id, timeout_processor_);
    assigned_pool_.erase(lookup_id);
  }

  bool apply_processor(int64 id, HttpRequestProcessor* request_processor) {
    void* context = ready_lookup_.addref_and_get(id);
    if (NULL == context) {
      // Must have timed out.
      return false;
    }
    ResponseContext* response_context = static_cast<ResponseContext*>(context);
    bool ok = response_context->apply_processor(request_processor);
    int deref_count = ok ? 2 : 1;
    ready_lookup_.deref(id, deref_count);
    return ok;
  }

  static void timer_callback(TimerCallbackContext context) {
    InnerHttpServer* http_server = reinterpret_cast<InnerHttpServer*>(
        context.value1);
    int64 lookup_id = context.value2;
    http_server->send_timeout_response(lookup_id);
  }

  DISALLOW_COPY_AND_ASSIGN(InnerHttpServer);
};

HttpServer::HttpServer(const char* host, const char* port,
                       int worker_thread_count, int max_latency_millis,
                       HttpRequestProcessor* timeout_processor)
    : inner_(new(std::nothrow) InnerHttpServer(
          host, port, worker_thread_count, max_latency_millis,
          timeout_processor)) {
}

HttpServer::~HttpServer() {
}

const char* HttpServer::get_url() {
  return inner_->get_url();
}

const char* HttpServer::get_actual_port() {
  return inner_->get_actual_port();
}

void HttpServer::run() {
  inner_->run();
}

void HttpServer::cancel() {
  inner_->cancel();
}

void HttpServer::set_max_latency_millis(int max_latency_millis) {
  inner_->set_max_latency_millis(max_latency_millis);
}

void HttpServer::checkout(HttpRequestProcessor* request_processor) {
  inner_->checkout(request_processor);
}

bool HttpServer::re_process(int64 id, HttpRequestProcessor* request_processor) {
  return inner_->re_process(id, request_processor);
}

}  // cc_net
