/*Implementation of Http Client.*/
#include "cc/net/http_client.h"
#include <errno.h>

using cc_shared::StringBuilder;
using std::string;
using std::vector;

namespace cc_net {

namespace {

// Retrieve the response as a series of non-blocking recv calls. Returns zero
// for success.
int32 retrieve_response(TcpConnectedSocket* connected_socket,
                        HttpParser* parser) {
  static const int kBufLen = 1024;
  char received[kBufLen];

  while (!(parser->get_completed())) {
    int bytes_received = 0;
    int32 result = connected_socket->receive_blocking(
        received, kBufLen, &bytes_received);
    if (0 != result) {
      return result;
    }
    if (0 == bytes_received) {
      return ECONNRESET;
    }
    CHECK_LT(0, bytes_received) << "Unexpected state.";
    parser->execute(received, bytes_received);
    if (!(parser->is_ok())) {
      return ENOTRECOVERABLE;
    }
  }
  return 0;
}

}  // namespace

HttpClient::HttpClient(const string& host, const string& port,
                       int timeout_milliseconds)
    : host_(host), port_(port),
      timeout_milliseconds_(timeout_milliseconds) {
  CHECK_LT(0, timeout_milliseconds_);
}

HttpClient::~HttpClient() {
}

int32 HttpClient::connect() {
  int result = socket_.initialize(host_, port_, timeout_milliseconds_);
  if (0 != result) {
    return result;
  }
  CHECK(socket_.get_blocking());
  return 0;
}

string HttpClient::get_client_address_port() {
  return socket_.get_local_address_port();
}

string HttpClient::get_server_address_port() {
  return socket_.get_remote_address_port();
}

void HttpClient::add_common_lines(
    const char* method, const string& url, bool keep_alive,
    StringBuilder* header_builder) {
  header_builder->append_c_str(method);
  header_builder->append_c_str(" ");
  header_builder->append(url.c_str(), url.size());
  header_builder->append_c_str(" HTTP/1.1\r\n");

  header_builder->append_c_str("Host: ");
  header_builder->append(host_.c_str(), host_.size());
  header_builder->append_c_str(":");
  header_builder->append(port_.c_str(), port_.size());
  header_builder->append_c_str("\r\n");

  if (keep_alive) {
    header_builder->append_c_str("Connection: keep-alive\r\n");
  } else {
    header_builder->append_c_str("Connection: close\r\n");
  }
}

void HttpClient::build_get_header(
    const std::string& url, bool keep_alive, StringBuilder* header_builder) {
  add_common_lines("GET", url, keep_alive, header_builder);
  header_builder->append_c_str("Accept: */*\r\n\r\n");
}

void HttpClient::build_post_header(
    const std::string& url, const std::string& content_type,
    const std::string& accepted_encoding, int byte_count, bool keep_alive,
    vector<HeaderType>* headers, StringBuilder* header_builder) {
  add_common_lines("POST", url, keep_alive, header_builder);
  char byte_count_text[100];
  sprintf(byte_count_text, "%d", byte_count);

  header_builder->append_c_str("Content-Length: ");
  header_builder->append_c_str(byte_count_text);
  header_builder->append_c_str("\r\n");

  header_builder->append_c_str("Content-Type: ");
  header_builder->append(content_type.c_str(), content_type.size());
  header_builder->append_c_str("\r\n");

  if (headers) {
    for (int i = 0; i < VSIZE(*headers); ++i) {
      header_builder->append_c_str((*headers)[i].first.c_str());
      header_builder->append_c_str(": ");
      header_builder->append_c_str((*headers)[i].second.c_str());
      header_builder->append_c_str("\r\n");
    }
  }

  header_builder->append_c_str("Accept-Encoding: ");
  header_builder->append(accepted_encoding.c_str(), accepted_encoding.size());
  header_builder->append_c_str("\r\n\r\n");
}


int32 HttpClient::send_get_request(const string& url, bool keep_alive,
                                   HttpParser* parser) {
  StringBuilder header_builder;
  build_get_header(url, keep_alive, &header_builder);
  parser->set_parse_response();
  parser->setup();
  int32 result = socket_.send_blocking(header_builder.c_str(),
                                       header_builder.get_str_len());
  if (0 != result) {
    return result;
  }
  return retrieve_response(&socket_, parser);
}

int32 HttpClient::send_post_request(
    const string& url, const string& content_type,
    const string& accepted_encoding, const char* payload, int byte_count,
    bool keep_alive, vector<HeaderType>* headers, HttpParser* parser) {
  parser->set_parse_response();
  parser->setup();
  StringBuilder payload_builder;
  build_post_header(url, content_type, accepted_encoding, byte_count,
                    keep_alive, headers, &payload_builder);
  payload_builder.append(payload, byte_count);
  int32 result = socket_.send_blocking(payload_builder.c_str(),
                                       payload_builder.get_str_len());
  if (0 != result) {
    return result;
  }
  return retrieve_response(&socket_, parser);
}

}  // cc_net
