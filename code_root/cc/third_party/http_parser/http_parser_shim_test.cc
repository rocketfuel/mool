// Unit tests for http parser.
#include "gtest/gtest.h"

extern "C" {
  void test_nginx_http_parser(void);
}

namespace cc_third_party_http_parser {

TEST(HttpParserTest, test_main) {
  test_nginx_http_parser();
}

}  // namespace cc_third_party_http_parser
