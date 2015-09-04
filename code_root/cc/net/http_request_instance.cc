/*Implementation of http request instance module.*/
#include "cc/net/http_request_instance.h"
#include <boost/lexical_cast.hpp>

namespace cc_net {

using cc_shared::BufferBuilder;
using std::string;

HttpRequestInstance::HttpRequestInstance(EpollServer* epoll_server,
                                         int64 connection_handle,
                                         HttpParser* parser,
                                         int64 instance_id,
                                         bool committed)
    : epoll_server_(epoll_server), connection_handle_(connection_handle),
      parser_(parser), instance_id_(instance_id), committed_(committed) {
}

HttpRequestInstance::~HttpRequestInstance() {
}

int64 HttpRequestInstance::get_id() {
  return instance_id_;
}

const char* HttpRequestInstance::get_http_method() {
  return parser_->get_http_method();
}

const char* HttpRequestInstance::get_http_version() {
  return parser_->get_http_version();
}

const char* HttpRequestInstance::get_url() {
  return parser_->get_url();
}

int HttpRequestInstance::get_header_count() {
  return parser_->get_header_count();
}

const char* HttpRequestInstance::get_header_name(int index) {
  return parser_->get_header_name(index);
}

const char* HttpRequestInstance::get_header_value(int index) {
  return parser_->get_header_value(index);
}

cc_shared::BufferBuilder::BufferInfo HttpRequestInstance::get_body_info() {
  return parser_->get_body_info();
}

void HttpRequestInstance::set_content_type(const char* content_type) {
  content_type_ = content_type;
}

void HttpRequestInstance::set_response_header(const char* name,
                                              const char* value) {
  headers_[name] = value;
}

void HttpRequestInstance::append_body(const char* buffer, int byte_count) {
  body_builder_.append(buffer, byte_count);
}

void HttpRequestInstance::append_body_text(const char* text) {
  append_body(text, static_cast<int32>(strlen(text)));
}

void HttpRequestInstance::build_header(BufferBuilder* header_builder) {
  string content_length = boost::lexical_cast<string>(
      body_builder_.get().length);
  header_builder->append_c_str("HTTP/1.1 200 OK\r\n");
  header_builder->append_c_str("Content-Length: ");
  header_builder->append_c_str(content_length.c_str());
  header_builder->append_c_str("\r\n");
  boost::unordered_map<string, string>::iterator iter;
  for (iter = headers_.begin(); iter != headers_.end(); ++iter) {
    header_builder->append_c_str(iter->first.c_str());
    header_builder->append_c_str(": ");
    header_builder->append_c_str(iter->second.c_str());
    header_builder->append_c_str("\r\n");
  }
  header_builder->append_c_str("\r\n");
}

void HttpRequestInstance::commit() {
  CHECK(!committed_) << "Cannot commit more than once.";
  BufferBuilder payload_builder;
  build_header(&payload_builder);
  payload_builder.append(body_builder_.get().ptr, body_builder_.get().length);
  // TODO: Break send into multiple calls if size is too big.
  epoll_server_->send_blocking(connection_handle_, payload_builder.get().ptr,
                               payload_builder.get().length);
  committed_ = true;
}

}  // cc_net
