/* Header file for http parsing.*/
#ifndef __CC_NET_HTTP_PARSER__
#define __CC_NET_HTTP_PARSER__

#include "cc/shared/common.h"
#include "cc/shared/scoped_ptr.h"
#include "cc/shared/string_builder.h"


namespace cc_net {

// Forward declaration.
class InnerParser;

// Light weight parser for Http requests and responses.
class HttpParser {
 public:
  HttpParser();

  ~HttpParser();

  // Setup.
  void set_parse_request();

  void set_parse_response();

  void set_expect_head_only(bool value);

  void setup();

  // Update.
  void execute(const char* data, size_t length);

  // Access state.
  bool get_completed();

  bool is_ok();

  int get_header_count();

  const char* get_header_name(int index);

  const char* get_header_value(int index);

  const char* get_url();

  // The buffer is mostly a string, but the http protocol does not expect it to
  // be NULL terminated.
  cc_shared::BufferBuilder::BufferInfo get_body_info();

  const char* get_response_reason();

  const char* get_http_method();

  int get_status_code();

  const char* get_http_version();

 private:
  cc_shared::scoped_ptr<InnerParser> inner_;
  bool parse_request_;
  bool expect_head_only_;
  DISALLOW_COPY_AND_ASSIGN(HttpParser);
};

// TODO: Consider publishing mechanism for URL parsing already present in
// third_party/http_parser.

}  // cc_net

#endif  // __CC_NET_HTTP_PARSER__
