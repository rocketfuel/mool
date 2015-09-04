/*Unit tests for Http parser module.*/
#include "cc/net/http_parser.h"

#include "gtest/gtest.h"

/*
NOTE: These tests form an extremely small subset of the complete set of tests
at cc/third_party/http_parser/http_parser_test.cc. Those tests execute the
parsing state machine (for HTTP requests, responses and URLs) for a much wider
variety of cases. These tests are present for (1) testing the callback logic
in the outer layer and (2) for illustrative purposes.
*/

using cc_shared::BufferBuilder;

namespace cc_net {

namespace {

// Break up a string into small parts and feed the parser. This mimics the
// behavior observed when bytes are read from a socket in separate parts.
void parse_by_parts(HttpParser* parser, const char* text,
                    bool check_completion_state) {
  static const int kChunkSize = 6;
  char buffer[kChunkSize];
  int bytes_left = strlen(text);
  const char* current = text;
  while (bytes_left > 0) {
    if (check_completion_state) {
      CHECK(!(parser->get_completed())) << "More bytes left to consume.";
    }
    int bytes_needed = std::min(bytes_left, kChunkSize);
    for (int i = 0; i < bytes_needed; ++i) {
      buffer[i] = current[i];
    }
    parser->execute(current, bytes_needed);
    current += bytes_needed;
    bytes_left -= bytes_needed;
  }
  if (check_completion_state) {
    CHECK(parser->get_completed()) << "Should have been done by now.";
  }
}

void validate_body(const char* text, BufferBuilder::BufferInfo info) {
  BufferBuilder builder;
  builder.append(info.ptr, info.length);
  builder.append_null_terminator();
  CHECK_EQ(static_cast<int>(1 + strlen(text)), builder.get().length);
  CHECK_EQ(0, strcmp(text, builder.get().ptr));
}

}  // namespace

TEST(HttpParserTest, test_get_request) {
  HttpParser parser;
  parser.set_parse_request();
  parser.setup();
  const char* kText = "GET /test HTTP/1.1\r\n"
                      "Accept: */*\r\n"
                      "\r\n";
  parse_by_parts(&parser, kText, true);
  EXPECT_EQ(0, parser.get_status_code());
  EXPECT_STREQ("1.1", parser.get_http_version());
  EXPECT_STREQ("GET", parser.get_http_method());
  EXPECT_STREQ("/test", parser.get_url());
  EXPECT_EQ(1, parser.get_header_count());
  EXPECT_STREQ("Accept", parser.get_header_name(0));
  EXPECT_STREQ("*/*", parser.get_header_value(0));
  validate_body("", parser.get_body_info());
  EXPECT_STREQ("", parser.get_response_reason());
}

TEST(HttpParserTest, test_post_request) {
  HttpParser parser;
  parser.set_parse_request();
  parser.setup();
  const char* kText = "POST /some_post_url?q=search#hey HTTP/1.1\r\n"
                      "Accept: */*\r\n"
                      "Transfer-Encoding: identity\r\n"
                      "Content-Length: 5\r\n"
                      "\r\n"
                      "World";
  parse_by_parts(&parser, kText, true);
  EXPECT_EQ(0, parser.get_status_code());
  EXPECT_STREQ("1.1", parser.get_http_version());
  EXPECT_STREQ("POST", parser.get_http_method());
  EXPECT_STREQ("/some_post_url?q=search#hey", parser.get_url());
  EXPECT_EQ(3, parser.get_header_count());
  EXPECT_STREQ("Accept", parser.get_header_name(0));
  EXPECT_STREQ("*/*", parser.get_header_value(0));
  EXPECT_STREQ("Transfer-Encoding", parser.get_header_name(1));
  EXPECT_STREQ("identity", parser.get_header_value(1));
  EXPECT_STREQ("Content-Length", parser.get_header_name(2));
  EXPECT_STREQ("5", parser.get_header_value(2));
  validate_body("World", parser.get_body_info());
  EXPECT_STREQ("", parser.get_response_reason());
}

TEST(HttpParserTest, test_failure_response) {
  HttpParser parser;
  parser.set_parse_response();
  parser.set_expect_head_only(false);
  parser.setup();
  const char* kText = "HTTP/1.1 301 Moved Permanently\r\n"
                      "Location: http://www.wherever.com/\r\n"
                      "Content-Type:  text/html; charset=UTF-8\r\n"
                      "X-$PrototypeBI-Version: 1.2.3.4\r\n"
                      "Content-Length: 7 \r\n"
                      "\r\n"
                      "<HTML/>";
  parse_by_parts(&parser, kText, true);
  EXPECT_EQ(301, parser.get_status_code());
  EXPECT_STREQ("1.1", parser.get_http_version());
  EXPECT_STREQ("", parser.get_url());
  EXPECT_EQ(4, parser.get_header_count());
  EXPECT_STREQ("Location", parser.get_header_name(0));
  EXPECT_STREQ("http://www.wherever.com/", parser.get_header_value(0));
  EXPECT_STREQ("Content-Type", parser.get_header_name(1));
  EXPECT_STREQ("text/html; charset=UTF-8", parser.get_header_value(1));
  EXPECT_STREQ("X-$PrototypeBI-Version", parser.get_header_name(2));
  EXPECT_STREQ("1.2.3.4", parser.get_header_value(2));
  EXPECT_STREQ("Content-Length", parser.get_header_name(3));
  EXPECT_STREQ("7 ", parser.get_header_value(3));
  EXPECT_STREQ("Moved Permanently", parser.get_response_reason());
  validate_body("<HTML/>", parser.get_body_info());
}

TEST(HttpParserTest, test_chunked_response) {
  HttpParser parser;
  parser.set_parse_response();
  parser.set_expect_head_only(false);
  parser.setup();
  const char* kText = "HTTP/1.1 200 OK\r\n"
                      "Content-Type: text/plain\r\n"
                      "Transfer-Encoding: chunked\r\n"
                      "\r\n"
                      "25  \r\n"
                      "This is the data in the first chunk\r\n"
                      "\r\n"
                      "1C\r\n"
                      "and this is the second one\r\n"
                      "\r\n"
                      "0  \r\n"
                      "\r\n";
  parse_by_parts(&parser, kText, true);
  EXPECT_EQ(200, parser.get_status_code());
  EXPECT_STREQ("1.1", parser.get_http_version());
  EXPECT_STREQ("", parser.get_url());
  EXPECT_EQ(2, parser.get_header_count());
  EXPECT_STREQ("Content-Type", parser.get_header_name(0));
  EXPECT_STREQ("text/plain", parser.get_header_value(0));
  EXPECT_STREQ("Transfer-Encoding", parser.get_header_name(1));
  EXPECT_STREQ("chunked", parser.get_header_value(1));
  EXPECT_STREQ("OK", parser.get_response_reason());
  validate_body("This is the data in the first chunk"
                "\r\nand this is the second one\r\n",
                parser.get_body_info());
}


TEST(HttpParserTest, test_head_only_response) {
  HttpParser parser;
  parser.set_parse_response();
  parser.set_expect_head_only(true);
  parser.setup();
  const char* kText = "HTTP/1.1 301 Moved Permanently\r\n"
                      "Location: http://www.wherever.com/\r\n"
                      "Content-Type:  text/html; charset=UTF-8\r\n"
                      "X-$PrototypeBI-Version: 1.2.3.4\r\n"
                      "Content-Length: 7 \r\n"
                      "\r\n"
                      "<HTML/>";
  parse_by_parts(&parser, kText, false);
  EXPECT_EQ(301, parser.get_status_code());
  EXPECT_STREQ("1.1", parser.get_http_version());
  EXPECT_STREQ("", parser.get_url());
  EXPECT_EQ(4, parser.get_header_count());
  EXPECT_STREQ("Location", parser.get_header_name(0));
  EXPECT_STREQ("http://www.wherever.com/", parser.get_header_value(0));
  EXPECT_STREQ("Content-Type", parser.get_header_name(1));
  EXPECT_STREQ("text/html; charset=UTF-8", parser.get_header_value(1));
  EXPECT_STREQ("X-$PrototypeBI-Version", parser.get_header_name(2));
  EXPECT_STREQ("1.2.3.4", parser.get_header_value(2));
  EXPECT_STREQ("Content-Length", parser.get_header_name(3));
  EXPECT_STREQ("7 ", parser.get_header_value(3));
  EXPECT_STREQ("Moved Permanently", parser.get_response_reason());
  validate_body("", parser.get_body_info());
}

}  // cc_net
