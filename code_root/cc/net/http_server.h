/*Header file for http server module.*/
#ifndef __CC_NET_HTTP_SERVER__
#define __CC_NET_HTTP_SERVER__

#include "cc/net/http_request_instance.h"
#include "cc/shared/common.h"
#include "cc/shared/scoped_ptr.h"

namespace cc_net {

// Forward declaration.
class InnerHttpServer;

// Callback interface provided by users of HttpServer.
class HttpRequestProcessor {
 public:
  virtual void process(HttpRequestInstance* request_instance) = 0;
};

class HttpServer {
 public:
  HttpServer(const char* host, const char* port, int worker_thread_count,
             int max_latency_millis, HttpRequestProcessor* timeout_processor);

  ~HttpServer();

  const char* get_url();

  const char* get_actual_port();

  // Http Server is already running and serving as soon as constructor returns.
  // It is possible (but not needed) to use a thread to "run" the server that
  // can be "cancelled" by another thread.
  void run();

  void cancel();

  void set_max_latency_millis(int max_latency_millis);

  // Check-out an Http Request to process. If the Http server has any available
  // requests to process then this is done in the same thread in a blocking
  // call. Otherwise the call returns.
  void checkout(HttpRequestProcessor* request_processor);

  // Caller needs to sometimes re-process a request instance with a given id.
  // This can be handled here. If return value is false then the id was not
  // found any more.
  bool re_process(int64 id, HttpRequestProcessor* request_processor);

 private:
  cc_shared::scoped_ptr<InnerHttpServer> inner_;
  DISALLOW_COPY_AND_ASSIGN(HttpServer);
};

}  // cc_net

#endif  // __CC_NET_HTTP_SERVER__
