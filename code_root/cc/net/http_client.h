/* Header file for http client.*/
#ifndef __CC_NET_HTTP_CLIENT__
#define __CC_NET_HTTP_CLIENT__

#include "cc/net/http_parser.h"
#include "cc/net/tcp_connected_socket.h"
#include "cc/shared/common.h"
#include "cc/shared/string_builder.h"

#include <algorithm>
#include <vector>

namespace cc_net {

class HttpClient {
 public:
  HttpClient(const std::string& host, const std::string& port,
             int timeout_milliseconds);
  ~HttpClient();

  int32 connect();

  std::string get_client_address_port();

  std::string get_server_address_port();

  // Sends the url to the remote server as a GET request, receives the response
  // and parses it into the provided parser object. Returns non-zero value if
  // there was a failure.
  int32 send_get_request(
      const std::string& url, bool keep_alive, HttpParser* parser);

  // Sends the url to the remote server as a POST request, receives the response
  // and parses it into the provided parser object. Returns non-zero value if
  // there was a failure.
  typedef std::pair<std::string, std::string> HeaderType;
  int32 send_post_request(
      const std::string& url, const std::string& content_type,
      const std::string& accepted_encoding, const char* payload, int byte_count,
      bool keep_alive, std::vector<HeaderType>* headers, HttpParser* parser);

 private:
  friend class HttpClientHeaderTest;
  TcpConnectedSocket socket_;
  std::string host_;
  std::string port_;
  int timeout_milliseconds_;

  // Header builder utility method.
  void add_common_lines(const char* method, const std::string& url,
                        bool keep_alive,
                        cc_shared::StringBuilder* header_builder);

  void build_get_header(const std::string& url, bool keep_alive,
                        cc_shared::StringBuilder* string_builder);

  void build_post_header(
      const std::string& url, const std::string& content_type,
      const std::string& accepted_encoding, int byte_count, bool keep_alive,
      std::vector<HeaderType>* headers,
      cc_shared::StringBuilder* string_builder);

  DISALLOW_COPY_AND_ASSIGN(HttpClient);
};

}  // cc_net

#endif  // __CC_NET_HTTP_CLIENT__
