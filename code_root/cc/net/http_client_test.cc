/*Unit tests for Http parser module.*/
#include "cc/net/http_client.h"
#include "gtest/gtest.h"

#include "cc/net/http_parser.h"
#include "cc/shared/scoped_ptr.h"

using cc_shared::StringBuilder;
using cc_shared::scoped_ptr;
using std::string;
using std::vector;

namespace cc_net {

class HttpClientHeaderTest : public testing::Test {
 protected:
  static const char* kHost;
  static const char* kPort;
  static const char* kUrl;
  static const char* kContentType;
  static const char* kAcceptedEncoding;
  static const int kByteCount;

  string get_get_header(bool keep_alive) {
    HttpClient http_client(kHost, kPort, 1);
    StringBuilder header_builder;
    http_client.build_get_header(kUrl, keep_alive, &header_builder);
    return header_builder.c_str();
  }

  string get_post_header(bool keep_alive) {
    HttpClient http_client(kHost, kPort, 1);
    StringBuilder header_builder;
    http_client.build_post_header(kUrl, kContentType, kAcceptedEncoding,
                                  kByteCount, keep_alive, NULL,
                                  &header_builder);
    return header_builder.c_str();
  }

  string get_post_header_with_additional_headers() {
    HttpClient http_client(kHost, kPort, 1);
    StringBuilder header_builder;
    vector<HttpClient::HeaderType> headers;
    headers.push_back(std::make_pair("h1", "v1"));
    headers.push_back(std::make_pair("h2", "v2"));
    http_client.build_post_header(kUrl, kContentType, kAcceptedEncoding,
                                  kByteCount, true, &headers,
                                  &header_builder);
    return header_builder.c_str();
  }
};

const char* HttpClientHeaderTest::kHost = "TEST_HOST";
const char* HttpClientHeaderTest::kPort = "TEST_PORT";
const char* HttpClientHeaderTest::kUrl = "TEST_URL";
const char* HttpClientHeaderTest::kContentType = "TEST_CONTENT";
const char* HttpClientHeaderTest::kAcceptedEncoding = "TEST_ENCODING";
const int HttpClientHeaderTest::kByteCount = 1234;

TEST_F(HttpClientHeaderTest, test_get_header_connection_close) {
  static const char* kExpected = "GET TEST_URL HTTP/1.1\r\n"
                                 "Host: TEST_HOST:TEST_PORT\r\n"
                                 "Connection: close\r\n"
                                 "Accept: */*\r\n\r\n";
  EXPECT_STREQ(kExpected, get_get_header(false).c_str());
}

TEST_F(HttpClientHeaderTest, test_get_header_connection_keep_alive) {
  static const char* kExpected = "GET TEST_URL HTTP/1.1\r\n"
                                 "Host: TEST_HOST:TEST_PORT\r\n"
                                 "Connection: keep-alive\r\n"
                                 "Accept: */*\r\n\r\n";
  EXPECT_STREQ(kExpected, get_get_header(true).c_str());
}

TEST_F(HttpClientHeaderTest, test_post_header_connection_close) {
  static const char* kExpected = "POST TEST_URL HTTP/1.1\r\n"
                                 "Host: TEST_HOST:TEST_PORT\r\n"
                                 "Connection: close\r\n"
                                 "Content-Length: 1234\r\n"
                                 "Content-Type: TEST_CONTENT\r\n"
                                 "Accept-Encoding: TEST_ENCODING\r\n\r\n";
  EXPECT_STREQ(kExpected, get_post_header(false).c_str());
}

TEST_F(HttpClientHeaderTest, test_post_header_connection_keep_alive) {
  static const char* kExpected = "POST TEST_URL HTTP/1.1\r\n"
                                 "Host: TEST_HOST:TEST_PORT\r\n"
                                 "Connection: keep-alive\r\n"
                                 "Content-Length: 1234\r\n"
                                 "Content-Type: TEST_CONTENT\r\n"
                                 "Accept-Encoding: TEST_ENCODING\r\n\r\n";
  EXPECT_STREQ(kExpected, get_post_header(true).c_str());
}

TEST_F(HttpClientHeaderTest, test_post_header_additional_headers) {
  static const char* kExpected = "POST TEST_URL HTTP/1.1\r\n"
                                 "Host: TEST_HOST:TEST_PORT\r\n"
                                 "Connection: keep-alive\r\n"
                                 "Content-Length: 1234\r\n"
                                 "Content-Type: TEST_CONTENT\r\n"
                                 "h1: v1\r\n"
                                 "h2: v2\r\n"
                                 "Accept-Encoding: TEST_ENCODING\r\n\r\n";
  EXPECT_STREQ(kExpected, get_post_header_with_additional_headers().c_str());
}

TEST(HttpClientTest, test_real_get_request) {
  // It would not be a good idea if Rocket Fuel unit tests started hammering
  // real servers on the internet. On the other hand, we would not have a good
  // http client if it could not communicate with a real Http Server out there.
  // We draw a compromise by enabling an end-to-end test that can be executed
  // manually, occasionally and periodically to ensure quality.
  bool e2e_mode = !!getenv("TCP_TEST_E2E_MODE");
  if (!e2e_mode) {
    return;
  }

  // Some servers (wikipedia, bing, amazon) honor connection keep-alive
  // requests.
  // Some others (yahoo.com and google.com) ignore keep-alive header.
  // Some redirect (yahoo.com & amazon).
  static const char* kHost = "en.wikipedia.org";
  static const char* kUrl = "/wiki/Main_Page";
  static const char* kPort = "80";

  static const int kTimeoutMillis = 2000;
  static const int kIntraRequestWaitMillis = 5;
  static const int kIterations = 3;  // pls do not make this too large
  static const bool kEchoParserDetails = false;

  HttpClient http_client(kHost, kPort, kTimeoutMillis);
  int32 result = http_client.connect();
  CHECK_EQ(0, result);
  LOG(INFO) << "Server details: " << http_client.get_server_address_port();
  LOG(INFO) << "Client details: " << http_client.get_client_address_port();
  for (int i = 0; i < kIterations; ++i) {
    HttpParser parser;
    LOG(INFO) << "Sending request.";
    result = http_client.send_get_request(kUrl, i < (kIterations - 1), &parser);
    CHECK_EQ(0, result);

    LOG(INFO) << "Received string of size " << parser.get_body_info().length
              << " bytes.";
    if (kEchoParserDetails) {
      std::cout << std::endl << std::endl
                << "Status code    : " << parser.get_status_code() << std::endl;
      std::cout << "Response reason: " << parser.get_response_reason()
                << std::endl;
      for (int i = 0; i < parser.get_header_count(); ++i) {
        std::cout << "H[" << parser.get_header_name(i) << "]: "
                  << parser.get_header_value(i) << std::endl;
      }
    }
    usleep(kIntraRequestWaitMillis * 1000);
  }
}

}  // cc_net
