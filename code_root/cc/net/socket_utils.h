/* Header file for socket utilities.*/
#ifndef __CC_NET_SOCKET_UTILS__
#define __CC_NET_SOCKET_UTILS__

#include "cc/shared/common.h"

#ifdef __gnu_linux__
#include <sys/epoll.h>
#endif  // __gnu_linux__

#define kInvalidSocket -1

namespace cc_net {

// All functions of socket utils return 0 for success and a non-zero errno
// number for failure.

class SocketUtils {
 public:
  static int32 initialize_stream_socket(
      const char* host, const char* port, bool can_accept, bool blocking,
      bool reuse_address, int timeout_milliseconds, int* sock_fd);

  static int32 close_socket(int sock_fd);

  static int32 get_ip_v4_name(int32 ip_v4_address, std::string* result);

  static int32 get_address_port_text(int32 ip_v4_address, int port,
                                     std::string* result);

  static int32 set_blocking(int sock_fd, bool blocking);

  static int32 set_nodelay(int sock_fd);

  static int32 set_reuse_address(int sock_fd, bool re_use);

  static int32 set_send_recv_timeout(int sock_fd, int timeout_milliseconds);

  static int32 get_sock_name(int sock_fd, int32* address, int32* port);

  static int32 get_peer_name(int sock_fd, int32* address, int32* port);

  static int32 select_wait(int sock_fd, int timeout_milliseconds);

  static int32 poll_for_read(int sock_fd, int timeout_milliseconds);

  static int32 poll_list_for_read(int* sock_fd_list, int list_length,
                                  int* out_sock_fd_list, int* out_list_length,
                                  int timeout_milliseconds);

  static int32 poll_for_write(int sock_fd, int timeout_milliseconds);

  static int32 accept_connection(int accepting_sock_fd, int* connected_sock_fd);

  static int32 receive_data_from_blocking_socket(
      int sock_fd, char* buffer, int buffer_len, int* bytes_received);

  static int32 send_data_over_blocking_socket(int sock_fd, const char* buffer,
                                              int buffer_len);

  static int32 receive_data_from_non_blocking_socket(
      int sock_fd, char* buffer, int buffer_len, int* bytes_received);

  static int32 send_data_over_non_blocking_socket(
      int sock_fd, const char* buffer, int buffer_len);

#ifdef __gnu_linux__
  static int32 create_epoll(int* epoll_fd);

  static int32 ctl_epoll(int epoll_fd, int target_fd, int64 callback_handle,
                         int operation, int events);

  static int32 wait_epoll(int epoll_fd, epoll_event* events, int max_events,
                          int timeout_millis, int* event_count);

#endif  // __gnu_linux__

 private:
  DISALLOW_DEFAULT_CONSTRUCTORS(SocketUtils);
};

}  // cc_net

#endif  // __CC_NET_SOCKET_UTILS__
