/*Header file for http request instance module.*/
#ifndef __CC_NET_HTTP_REQUEST_INSTANCE__
#define __CC_NET_HTTP_REQUEST_INSTANCE__

#include "cc/net/epoll_server.h"
#include "cc/net/http_parser.h"
#include "cc/shared/common.h"
#include "cc/shared/string_builder.h"

#include <boost/unordered_map.hpp>

namespace cc_net {

class HttpRequestInstance {
 public:
  HttpRequestInstance(EpollServer* epoll_server,
                      int64 connection_handle, HttpParser* parser,
                      int64 instance_id, bool committed);

  ~HttpRequestInstance();

  // Reader methods.
  int64 get_id();
  const char* get_http_method();
  const char* get_http_version();
  const char* get_url();
  int get_header_count();
  const char* get_header_name(int index);
  const char* get_header_value(int index);
  cc_shared::BufferBuilder::BufferInfo get_body_info();

  bool get_committed() {
    return committed_;
  }

  // Writer methods.
  void set_content_type(const char* content_type);
  void set_response_header(const char* name, const char* value);
  void append_body(const char* buffer, int byte_count);
  void append_body_text(const char* text);
  void commit();

 private:
  // State & callback fields.
  EpollServer* epoll_server_;
  int64 connection_handle_;
  HttpParser* parser_;
  int64 instance_id_;
  bool committed_;

  // Response construction fields.
  boost::unordered_map<std::string, std::string> headers_;
  cc_shared::BufferBuilder body_builder_;
  std::string content_type_;

  void build_header(cc_shared::BufferBuilder* header_builder);

  DISALLOW_COPY_AND_ASSIGN(HttpRequestInstance);
};

}  // cc_net

#endif  // __CC_NET_HTTP_REQUEST_INSTANCE__
