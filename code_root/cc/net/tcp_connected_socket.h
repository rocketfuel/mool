/*Header file for tcp connected socket.*/
#ifndef __CC_NET_TCP_CONNECTED_SOCKET__
#define __CC_NET_TCP_CONNECTED_SOCKET__

#include "cc/shared/common.h"

namespace cc_net {

class TcpConnectedSocket {
 public:
  TcpConnectedSocket();

  ~TcpConnectedSocket();

  // If initialization fails, return value is non-zero.
  int32 initialize(const std::string& host, const std::string& port,
                   int timeout_milliseconds);

  int32 get_remote_address() {
    return remote_address_;
  }

  int32 get_remote_port() {
    return remote_port_;
  }

  int32 get_local_address() {
    return local_address_;
  }

  int32 get_local_port() {
    return local_port_;
  }

  std::string get_local_address_port();

  std::string get_remote_address_port();

  // Can be re-initialized after closing.
  void close_socket();

  int32 set_blocking(int timeout_milliseconds);

  int32 get_blocking() {
    return is_blocking_;
  }

  // Tries to send the whole buffer. If there are any failures, non-zero value
  // is returned and socket should be closed.
  int32 send_blocking(const char* buffer, int buffer_len);

  // Returns non-zero if socket should be closed. bytes_received is filled out
  // with number of bytes received. If bytes_received is zero, socket should be
  // closed as it has been closed on the other side.
  int32 receive_blocking(char* buffer, int buffer_len, int* bytes_received);

 private:
  int native_socket_;
  int32 local_address_;
  int32 local_port_;
  int32 remote_address_;
  int32 remote_port_;
  bool is_blocking_;

  int32 load_address_port_info();

  DISALLOW_COPY_AND_ASSIGN(TcpConnectedSocket);
};

}  // cc_net

#endif  // __CC_NET_TCP_CONNECTED_SOCKET__
