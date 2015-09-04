/*Implementation of Http Parser.*/
// Enable for miscellaneous logging.
// #define CC_TRACE_ENABLED
#include "cc/net/http_parser.h"
#include "cc/shared/string_builder.h"
#include "cc/third_party/http_parser/http_parser.h"

#include <vector>

using cc_shared::BufferBuilder;
using cc_shared::StringBuilder;
using std::vector;
using std::string;

namespace cc_net {

// We need a lot of boilerplate code because the handler callbacks only pass a
// a pointer to the parser structure. We have to guess the "this" pointer from
// the value of the pointer to the parser structure.
#define HTTP_PARSER_STATIC_CALLBACK(_name) \
  static int _name##_static(http_parser* parser) { \
    InnerParser* this_ = static_cast<InnerParser*>(parser->data); \
    return this_->_name(); \
  }

#define HTTP_PARSER_STATIC_DATA_CALLBACK(_name) \
  static int _name##_static(http_parser* parser, const char* read_ptr, \
                            size_t length) { \
    InnerParser* this_ = static_cast<InnerParser*>(parser->data); \
    return this_->_name(read_ptr, length); \
  }

#define HTTP_PARSER_ASSIGN_CALLBACK(_name) { \
  parser_settings_._name = _name ## _static; \
}

// A macro to generate other macros. XX_CB and XX_DATA_CB are other appropriate
// macros.
#define HTTP_PARSER_MACRO_GENERATOR(XX_CB, XX_DATA_CB) \
  XX_CB(on_message_begin) \
  XX_CB(on_message_complete) \
  XX_DATA_CB(on_url) \
  XX_DATA_CB(on_header_field) \
  XX_DATA_CB(on_header_value) \
  XX_DATA_CB(on_headers_complete) \
  XX_DATA_CB(on_body) \
  XX_DATA_CB(on_reason) \
  XX_CB(on_chunk_header) \
  XX_CB(on_chunk_complete)

namespace {

enum {
  kNone,
  kField,
  kValue
};

}  // namespace


class InnerParser {
 public:
  InnerParser(bool parse_request, bool expect_head_only)
      : last_header_element_(kNone), expect_head_only_(expect_head_only),
        http_major_(-1), http_minor_(-1), status_code_(-1), completed_(false) {
    init_parser_settings();
    ZERO_MEMORY(&parser_, sizeof(parser_));
    http_parser_init(&parser_, (parse_request ? HTTP_REQUEST : HTTP_RESPONSE));
    parser_.data = static_cast<void*>(this);
  }

  ~InnerParser() {
    DELETE_POINTER_VECTOR(header_names_);
    DELETE_POINTER_VECTOR(header_values_);
  }

  void execute(const char* data, size_t length) {
    http_parser_execute(&parser_, &parser_settings_, data, length);
  }

  bool get_completed() {
    return completed_;
  }

  bool is_ok() {
    bool ok = (HPE_OK == HTTP_PARSER_ERRNO(&parser_));
    if (!ok) {
      TRACE_FILE_EVENT((completed_ ? "Complete: " : "Incomplete: ")
                       << HTTP_PARSER_ERRNO(&parser_) << " "
                       << http_errno_name(HTTP_PARSER_ERRNO(&parser_)));
    }
    return ok;
  }

  int get_header_count() {
    CHECK_EQ(VSIZE(header_names_), VSIZE(header_values_));
    return VSIZE(header_names_);
  }

  const char* get_header_name(int index) {
    return header_names_[index]->c_str();
  }

  const char* get_header_value(int index) {
    return header_values_[index]->c_str();
  }

  const char* get_url() {
    return url_.c_str();
  }

  cc_shared::BufferBuilder::BufferInfo get_body_info() {
    return body_.get();
  }

  const char* get_response_reason() {
    return response_reason_.c_str();
  }

  const char* get_http_method() {
    return http_method_str((http_method) http_method_);
  }

  int get_status_code() {
    return status_code_;
  }

  const char* get_http_version() {
    return http_version_.c_str();
  }

 private:
  http_parser parser_;
  http_parser_settings parser_settings_;

  vector<StringBuilder*> header_names_;
  vector<StringBuilder*> header_values_;
  StringBuilder url_;
  BufferBuilder body_;
  StringBuilder response_reason_;
  int last_header_element_;
  bool expect_head_only_;
  int http_method_;
  int http_major_;
  int http_minor_;
  int status_code_;
  bool completed_;
  std::string http_version_;

  int on_url(const char* read_ptr, size_t length) {
    url_.append(read_ptr, length);
    return 0;
  }

  int on_header_field(const char* read_ptr, size_t length) {
    if (last_header_element_ != kField) {
      header_names_.push_back(new(std::nothrow) StringBuilder());
      header_values_.push_back(new(std::nothrow) StringBuilder());
    }
    header_names_[VSIZE(header_names_) - 1]->append(read_ptr, length);
    last_header_element_ = kField;
    return 0;
  }

  int on_header_value(const char* read_ptr, size_t length) {
    header_values_[VSIZE(header_values_) - 1]->append(read_ptr, length);
    last_header_element_ = kValue;
    return 0;
  }

  int on_headers_complete(const char* read_ptr, size_t length) {
    CHECK(!read_ptr) << "Did not expect any more characters from parser.";
    http_method_ = parser_.method;
    status_code_ = parser_.status_code;
    http_major_ = parser_.http_major;
    http_minor_ = parser_.http_minor;
    char buffer[200];
    ZERO_ARRAY(buffer);
    sprintf(buffer, "%d.%d", parser_.http_major, parser_.http_minor);
    http_version_ = buffer;
    if (expect_head_only_) {
      return 1;
    }
    return 0;
  }

  int on_body(const char* read_ptr, size_t length) {
    body_.append(read_ptr, length);
    return 0;
  }

  int on_reason(const char* read_ptr, size_t length) {
    response_reason_.append(read_ptr, length);
    return 0;
  }

  int on_message_begin() {
    // NO OP.
    return 0;
  }

  int on_message_complete() {
    completed_ = true;
    return 0;
  }

  int on_chunk_header() {
    // NO OP.
    return 0;
  }

  int on_chunk_complete() {
    // NO OP.
    return 0;
  }

  HTTP_PARSER_MACRO_GENERATOR(HTTP_PARSER_STATIC_CALLBACK,
                              HTTP_PARSER_STATIC_DATA_CALLBACK);
  void init_parser_settings() {
    HTTP_PARSER_MACRO_GENERATOR(HTTP_PARSER_ASSIGN_CALLBACK,
                                HTTP_PARSER_ASSIGN_CALLBACK);
  }
  DISALLOW_COPY_AND_ASSIGN(InnerParser);
};

#undef HTTP_PARSER_STATIC_CALLBACK
#undef HTTP_PARSER_STATIC_DATA_CALLBACK
#undef HTTP_PARSER_ASSIGN_CALLBACK
#undef HTTP_PARSER_MACRO_GENERATOR

HttpParser::HttpParser() : parse_request_(true), expect_head_only_(false) {
}

void HttpParser::set_parse_request() {
  parse_request_ = true;
}

void HttpParser::set_parse_response() {
  parse_request_ = false;
}

void HttpParser::set_expect_head_only(bool value) {
  CHECK(!parse_request_) << "Applies for responses only.";
  expect_head_only_ = value;
}

void HttpParser::setup() {
  CHECK(!inner_.get()) << "Cannot reuse object.";
  inner_.replace(new(std::nothrow)
      InnerParser(parse_request_, expect_head_only_));
}

HttpParser::~HttpParser() {
}

void HttpParser::execute(const char* data, size_t length) {
  inner_->execute(data, length);
}

bool HttpParser::get_completed() {
  return inner_->get_completed();
}

bool HttpParser::is_ok() {
  return inner_->is_ok();
}

int HttpParser::get_header_count() {
  return inner_->get_header_count();
}

const char* HttpParser::get_header_name(int index) {
  return inner_->get_header_name(index);
}

const char* HttpParser::get_header_value(int index) {
  return inner_->get_header_value(index);
}

const char* HttpParser::get_url() {
  return inner_->get_url();
}

cc_shared::BufferBuilder::BufferInfo HttpParser::get_body_info() {
  return inner_->get_body_info();
}

const char* HttpParser::get_response_reason() {
  return inner_->get_response_reason();
}

const char* HttpParser::get_http_method() {
  return inner_->get_http_method();
}

int HttpParser::get_status_code() {
  return inner_->get_status_code();
}

const char* HttpParser::get_http_version() {
  return inner_->get_http_version();
}

}  // cc_net
