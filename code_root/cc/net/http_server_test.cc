/*Unit test for http server module.*/
#include "cc/net/http_server.h"
#include "cc/net/http_client.h"
#include "cc/net/http_parser.h"
#include "cc/shared/string_builder.h"

#include "gtest/gtest.h"

#include <string>
#include <boost/atomic.hpp>
#include <boost/bind.hpp>
#include <boost/thread/thread.hpp>

using cc_shared::scoped_ptr;
using cc_shared::BufferBuilder;
using std::string;

namespace cc_net {

static const char* kTimeoutPayload[] = {"Timed", " Out"};

static const char* kPullerPayload[] = {
    "<html>", "<body><h1>Hello, World</h1></body>", "</html>"
};

class TestProcessor : public HttpRequestProcessor {
 public:
  TestProcessor() : do_read_(true), do_write_(false), last_id_(-1),
                    new_id_(false), save_id_(true),
                    write_timeout_payload_(false) {
  }

  virtual ~TestProcessor() {
  }

  void do_read(HttpRequestInstance* request_instance) {
    if (save_id_) {
      CHECK_LE(0, request_instance->get_id());
    }
    CHECK(request_instance->get_url());
    CHECK(request_instance->get_http_method());
    int total = request_instance->get_header_count();
    for (int i = 0; i < total; ++i) {
      CHECK(request_instance->get_header_name(i));
      CHECK(request_instance->get_header_value(i));
    }
    if (save_id_) {
      CHECK(!new_id_);
      last_id_ = request_instance->get_id();
      new_id_ = true;
    }
  }

  void do_write(HttpRequestInstance* request_instance) {
    request_instance->set_content_type("text/html; charset=UTF-8");
    request_instance->set_response_header("header1", "value1");
    request_instance->set_response_header("header2", "value2");
    if (write_timeout_payload_) {
      for (int i = 0; i < ARRAY_SIZE(kTimeoutPayload); ++i) {
        request_instance->append_body_text(kTimeoutPayload[i]);
      }
    } else {
      for (int i = 0; i < ARRAY_SIZE(kPullerPayload); ++i) {
        request_instance->append_body_text(kPullerPayload[i]);
      }
    }
    request_instance->commit();
  }

  virtual void process(HttpRequestInstance* request_instance) {
    if (do_read_) {
      do_read(request_instance);
    }
    if (do_write_) {
      do_write(request_instance);
    }
  }

  void set_read(bool value) {
    do_read_ = value;
  }

  void set_write(bool value) {
    do_write_ = value;
  }

  void set_save_id(bool value) {
    save_id_ = value;
  }

  void set_write_timeout_payload(bool value) {
    write_timeout_payload_ = value;
  }

  int64 get_last_id() {
    return last_id_;
  }

  bool get_new_id() {
    return new_id_;
  }

 private:
  bool do_read_;
  bool do_write_;
  int64 last_id_;
  bool new_id_;
  bool save_id_;
  bool write_timeout_payload_;
  DISALLOW_COPY_AND_ASSIGN(TestProcessor);
};

class HttpServerTest : public testing::Test {
 protected:
  static const char kHost[];
  static const char kDefaultPort[];
  static const int kWorkerThreadCount;
  static const int kDefaultLatencyMillis;

  scoped_ptr<HttpServer> http_server_;
  scoped_ptr<boost::thread_group> server_puller_threads_;
  std::string expected_;
  std::string timeout_response_;
  TestProcessor timeout_processor_;

  bool validate_response_;
  int average_processing_millis_;
  boost::atomic<int64> timeout_count_;
  boost::atomic<int64> specific_count_;

  HttpServerTest()
      : server_puller_threads_(new boost::thread_group),
        validate_response_(true), average_processing_millis_(0),
        timeout_count_(0), specific_count_(0) {
    timeout_processor_.set_write(true);
    timeout_processor_.set_write_timeout_payload(true);
    timeout_processor_.set_save_id(false);
  }

  void start_server(int worker_thread_count) {
    CHECK(NULL == http_server_.get());
    http_server_.replace(
        new (std::nothrow) HttpServer(kHost, kDefaultPort, worker_thread_count,
                                      kDefaultLatencyMillis,
                                      &timeout_processor_));
    for (int i = 0; i < ARRAY_SIZE(kTimeoutPayload); ++i) {
      expected_ += kTimeoutPayload[i];
    }
    timeout_response_ = expected_;
  }

  ~HttpServerTest() {
    if (http_server_.get()) {
      http_server_->cancel();
    }
    server_puller_threads_->interrupt_all();
    server_puller_threads_->join_all();
  }

  void prepare_for_non_zero_pullers() {
    expected_ = "";
    for (int i = 0; i < ARRAY_SIZE(kPullerPayload); ++i) {
      expected_ += kPullerPayload[i];
    }
    // Increase the default latency during unit tests. This is needed because
    // unit tests do not run with dedicated resources like production machines.
    // We need to make sure that the pullers win the race over the default
    // completion thread.
    http_server_->set_max_latency_millis(200);
  }

  void add_pullers(int puller_thread_count) {
    for (int i = 0; i < puller_thread_count; ++i) {
      server_puller_threads_->create_thread(
          boost::bind(&HttpServerTest::puller_worker, this));
    }
    prepare_for_non_zero_pullers();
  }

  void puller_worker() {
    while (!boost::this_thread::interruption_requested()) {
      TestProcessor re_processor;
      re_processor.set_read(true);
      re_processor.set_write(true);
      http_server_->checkout(&re_processor);
      usleep(1000);
    }
  }

  void add_reprocessor_puller() {
    server_puller_threads_->create_thread(
        boost::bind(&HttpServerTest::reprocessor_puller_worker, this));
    prepare_for_non_zero_pullers();
  }

  void reprocessor_puller_worker() {
    while (!boost::this_thread::interruption_requested()) {
      TestProcessor re_processor;
      re_processor.set_read(true);
      re_processor.set_write(false);
      http_server_->checkout(&re_processor);
      if (re_processor.get_new_id()) {
        re_processor.set_write(true);
        re_processor.set_read(false);
        http_server_->re_process(re_processor.get_last_id(),
                                 &re_processor);
      }
      usleep(1000);
    }
  }

  void validate_response(const char* actual) {
    if (validate_response_) {
      ASSERT_STREQ(expected_.c_str(), actual);
    }
  }

  void single_client_run(int index, int iteration_count) {
    static const int kTimeoutMillis = 500;
    static const char* kPostContentType = "application/octet-stream";
    static const char* kAcceptedEncoding = "gzip/deflate";
    static const char kPostPayload[] = "Some message.";
    static const int kPostPayloadSize = ARRAY_SIZE(kPostPayload) - 1;
    bool do_get = 0 == (index % 2);
    HttpClient client(kHost, http_server_->get_actual_port(), kTimeoutMillis);
    int result = client.connect();
    CHECK_EQ(0, result);
    string url = "/first/second";
    for (int i = 0; i < iteration_count; ++i) {
      HttpParser parser;
      if (do_get) {
        result = client.send_get_request(
            url, i < (iteration_count - 1), &parser);
        CHECK_EQ(0, result);
      } else {
        result = client.send_post_request(
            url, kPostContentType, kAcceptedEncoding, kPostPayload,
            kPostPayloadSize, i < (iteration_count - 1), NULL, &parser);
        CHECK_EQ(0, result);
      }
      BufferBuilder builder;
      builder.append(parser.get_body_info().ptr, parser.get_body_info().length);
      builder.append_null_terminator();
      validate_response(builder.get().ptr);
      if (0 == strcmp(builder.get().ptr, timeout_response_.c_str())) {
        ++timeout_count_;
      } else {
        ++specific_count_;
      }
    }
  }

  void test_multiple_client_threads(int thread_count, int iteration_count) {
    boost::thread_group client_threads;
    for (int i = 0; i < thread_count; ++i) {
      client_threads.create_thread(
          boost::bind(&HttpServerTest::single_client_run, this, i,
                      iteration_count));
    }
    client_threads.join_all();
  }

  void heavy_puller_worker() {
    while (!boost::this_thread::interruption_requested()) {
      TestProcessor re_processor;
      re_processor.set_read(true);
      re_processor.set_write(false);
      http_server_->checkout(&re_processor);
      if (re_processor.get_new_id()) {
        // Time for some heavy lifting.
        int error = (rand() % 16) - 8;
        int sleep_millis = error + average_processing_millis_;
        CHECK(sleep_millis > 0)
            << "average_processing_millis_ cannot be too low.";
        usleep(sleep_millis * 1000);

        re_processor.set_write(true);
        re_processor.set_read(false);
        http_server_->re_process(re_processor.get_last_id(),
                                 &re_processor);
      } else {
        usleep(1000);
      }
    }
  }

  void perform_test(int io_thread_count, int puller_thread_count,
                    int client_thread_count, int client_iteration_count,
                    int max_latency_millis,
                    int average_processing_millis,
                    double expected_min_specific_percentage,
                    double expected_max_specific_percentage) {
    // Only run this test when enabled.
    bool e2e_mode = !!getenv("HTTP_TEST_E2E_MODE");
    if (!e2e_mode) {
      return;
    }
    timeout_count_ = 0;
    specific_count_ = 0;
    average_processing_millis_ = average_processing_millis;
    validate_response_ = false;
    start_server(io_thread_count);
    http_server_->set_max_latency_millis(max_latency_millis);
    for (int i = 0; i < puller_thread_count; ++i) {
      server_puller_threads_->create_thread(
          boost::bind(&HttpServerTest::heavy_puller_worker, this));
    }
    boost::thread_group client_threads;
    for (int i = 0; i < client_thread_count; ++i) {
      client_threads.create_thread(
          boost::bind(&HttpServerTest::single_client_run, this, i,
                      client_iteration_count));
    }
    client_threads.join_all();
    int64 total_responses = timeout_count_ + specific_count_;
    double specific_percentage = 100.0 * specific_count_ / total_responses;
    bool ok = ((expected_min_specific_percentage <= specific_percentage) &&
               (specific_percentage <= expected_max_specific_percentage));
    if (!ok) {
      LOG(INFO) << "Non-Timeout rate = " << specific_percentage << "% ("
                << specific_count_ << " / " << total_responses << ")";
    }
    EXPECT_LE(expected_min_specific_percentage, specific_percentage);
    EXPECT_LE(specific_percentage, expected_max_specific_percentage);
  }

 private:
  DISALLOW_COPY_AND_ASSIGN(HttpServerTest);
};

const char HttpServerTest::kHost[] = "127.0.0.1";
const char HttpServerTest::kDefaultPort[] = "0";
const int HttpServerTest::kWorkerThreadCount = 2;
const int HttpServerTest::kDefaultLatencyMillis = 10;

TEST_F(HttpServerTest, test_simple_with_timeout) {
  start_server(kWorkerThreadCount);
  single_client_run(0, 4);
}

TEST_F(HttpServerTest, test_parallel_with_timeout) {
  start_server(kWorkerThreadCount);
  test_multiple_client_threads(6, 100);
}

TEST_F(HttpServerTest, test_simple_with_pullers) {
  start_server(kWorkerThreadCount);
  add_pullers(2);
  single_client_run(0, 4);
}

TEST_F(HttpServerTest, test_parallel_with_pullers) {
  start_server(kWorkerThreadCount);
  add_pullers(10);
  test_multiple_client_threads(6, 150);
}

TEST_F(HttpServerTest, test_re_process) {
  start_server(kWorkerThreadCount);
  add_reprocessor_puller();
  single_client_run(0, 4);
}

TEST_F(HttpServerTest, test_fast_pullers) {
  perform_test(2,      // i/o thread count
               10,     // puller thread count
               5,      // client thread count
               200,    // client thread iterations
               30,     // max_latency_millis
               10,     // average_processing_millis
               95.0,   // expected_min_specific_percentage
               100.0   // expected_max_specific_percentage
               );
}

TEST_F(HttpServerTest, test_contention) {
  perform_test(2,      // i/o thread count
               10,     // puller thread count
               5,      // client thread count
               200,    // client thread iterations
               20,     // max_latency_millis
               20,     // average_processing_millis
               25.0,   // expected_min_specific_percentage
               65.0    // expected_max_specific_percentage
               );
}

TEST_F(HttpServerTest, test_slow_pullers) {
  perform_test(2,      // i/o thread count
               10,     // puller thread count
               5,      // client thread count
               200,    // client thread iterations
               10,     // max_latency_millis
               15,     // average_processing_millis
               5.0,    // expected_min_specific_percentage
               50.0    // expected_max_specific_percentage
               );
}

TEST_F(HttpServerTest, test_very_slow_pullers) {
  perform_test(2,      // i/o thread count
               10,     // puller thread count
               5,      // client thread count
               200,    // client thread iterations
               10,     // max_latency_millis
               22,     // average_processing_millis
               0.0,    // expected_min_specific_percentage
               5.0     // expected_max_specific_percentage
               );
}

}  // cc_net
