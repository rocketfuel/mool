/*Implementation of Socket utilities.*/
#include "cc/net/socket_utils.h"

#include "cc/shared/scoped_array.h"

#include <arpa/inet.h>
#include <errno.h>
#include <fcntl.h>
#include <netdb.h>
#include <netinet/tcp.h>
#include <sys/poll.h>
#include <sys/socket.h>
#include <unistd.h>

#define TRACE_ERRORS_IN_FILE 0

#if TRACE_ERRORS_IN_FILE
// Save errno so that LOG() cannot change it accidentally.
#define TRACE_FAILURE_LOCATION  {     \
  int en = errno;                     \
  LOG(INFO) << "Failed here with '"   \
            << strerror(en) << "': "  \
            << en;                    \
  errno = en;                         \
}
#else
#define TRACE_FAILURE_LOCATION
#endif  // TRACE_ERRORS_IN_FILE

using std::string;

#define CHECK_AND_RETURN_ERRNO(_condition)  \
  if (!(_condition)) {                      \
    int ee = errno;                         \
    TRACE_FAILURE_LOCATION;                 \
    CHECK_NE(0, ee);                        \
    return ee;                              \
  }

#define CHECK_AND_RETURN_SPECIFIC_ERRNO(_condition, _errval)  \
  if (!(_condition)) {                                        \
    errno = (_errval);                                        \
    CHECK_AND_RETURN_ERRNO(false);                            \
  }

#ifndef __gnu_linux__
#define MSG_NOSIGNAL 0
#define SOL_TCP IPPROTO_TCP
#endif  // __gnu_linux__


namespace cc_net {

namespace {

class AddressInfo {
 public:
  AddressInfo(const char* host, const char* port) : server_list_(NULL) {
    addrinfo hints;
    ZERO_MEMORY(&hints, sizeof(hints));
    hints.ai_family = AF_INET;
    hints.ai_socktype = SOCK_STREAM;
    int result = getaddrinfo(host, port, &hints, &server_list_);
    CHECK(0 == result) << "getaddrinfo failed: '" << gai_strerror(result);
  }

  ~AddressInfo() {
    if (server_list_) {
      freeaddrinfo(server_list_);
      server_list_ = NULL;
    }
  }

  addrinfo* get_server_list() {
    return server_list_;
  }

 private:
  addrinfo* server_list_;
  DISALLOW_COPY_AND_ASSIGN(AddressInfo);
};

// "Non-blocking connect" copied from lib/connect_nonb.c at
// http://www.unpbook.com/src.html.
// Does not close the socket in error case.
int32 connect_non_blocking(
    int sock_fd, const sockaddr* sa_ptr,
    socklen_t sa_len, int timeout_milliseconds) {
  int32 result = 0;
  int error = 0;

  do {
    result = SocketUtils::set_blocking(sock_fd, false);
    CHECK_AND_RETURN_SPECIFIC_ERRNO(0 == result, result);

    int connect_result = connect(sock_fd, sa_ptr, sa_len);
    error = errno;
    if (0 != connect_result) {
      CHECK(connect_result < 0) << "Unexpected";
      CHECK_AND_RETURN_ERRNO(error == EINPROGRESS);

      result = SocketUtils::select_wait(sock_fd, timeout_milliseconds);
      CHECK_AND_RETURN_SPECIFIC_ERRNO(0 == result, result);

      socklen_t len = sizeof(error);
      result = getsockopt(sock_fd, SOL_SOCKET, SO_ERROR, &error, &len);
      CHECK_AND_RETURN_ERRNO(result >= 0);
    }

    result = SocketUtils::set_blocking(sock_fd, true);
    CHECK_AND_RETURN_SPECIFIC_ERRNO(0 == result, result);
  } while (false);

  return result;
}

int32 socket_initialize(int sock_fd, addrinfo* curr, bool reuse_address,
                        bool can_accept, int timeout_milliseconds) {
  int result = 0;

  result = SocketUtils::set_send_recv_timeout(sock_fd, timeout_milliseconds);
  CHECK_AND_RETURN_SPECIFIC_ERRNO(0 == result, result);

  result = SocketUtils::set_reuse_address(sock_fd, reuse_address);
  CHECK_AND_RETURN_SPECIFIC_ERRNO(0 == result, result);

  result = SocketUtils::set_nodelay(sock_fd);
  CHECK_AND_RETURN_SPECIFIC_ERRNO(0 == result, result);

  if (can_accept) {
    result = bind(sock_fd, curr->ai_addr, curr->ai_addrlen);
  } else {
    result = connect_non_blocking(
        sock_fd, curr->ai_addr, curr->ai_addrlen, timeout_milliseconds);
  }
  CHECK_AND_RETURN_ERRNO(-1 != result);
  return 0;
}

}  // namespace

int32 SocketUtils::initialize_stream_socket(
    const char* host, const char* port, bool can_accept, bool blocking,
    bool reuse_address, int timeout_milliseconds, int* sock_fd) {
  AddressInfo addresses(host, port);
  addrinfo* curr = NULL;
  int result = 0;
  (*sock_fd) = kInvalidSocket;

  for (curr = addresses.get_server_list(); curr != NULL; curr = curr->ai_next) {
    int temp_sock_fd = socket(curr->ai_family, curr->ai_socktype,
                              curr->ai_protocol);
    result = socket_initialize(temp_sock_fd, curr, reuse_address, can_accept,
                               timeout_milliseconds);
    if (0 == result) {
      (*sock_fd) = temp_sock_fd;
      break;
    }
  }
  CHECK_AND_RETURN_SPECIFIC_ERRNO(NULL != curr, ENOTCONN);
  result = set_blocking((*sock_fd), blocking);
  CHECK_AND_RETURN_SPECIFIC_ERRNO(0 == result, result);
  if (can_accept) {
    result = listen((*sock_fd), SOMAXCONN);
    CHECK_AND_RETURN_ERRNO(0 == result);
  }
  return 0;
}

int32 SocketUtils::close_socket(int sock_fd) {
  if (sock_fd != kInvalidSocket) {
    int result = close(sock_fd);
    CHECK_AND_RETURN_ERRNO(0 == result);
  }
  return 0;
}

int32 SocketUtils::get_ip_v4_name(int32 ip_v4_address, string* result) {
  char result_text[INET_ADDRSTRLEN + 1];
  ZERO_MEMORY(result_text, sizeof(result_text));

  struct sockaddr_in sa;
  ZERO_MEMORY(&sa, sizeof(sa));
  sa.sin_addr.s_addr = htonl(ip_v4_address);

  const char* rv = inet_ntop(AF_INET, &(sa.sin_addr), result_text,
                             INET_ADDRSTRLEN);
  CHECK_AND_RETURN_ERRNO(rv == result_text);
  (*result) = result_text;
  return 0;
}

int32 SocketUtils::get_address_port_text(int32 ip_v4_address, int port,
                                         string* result) {
  static const int kMaxDigits = 100;
  char port_text[kMaxDigits];
  sprintf(port_text, "%d", port);

  string address_text;
  int rv = get_ip_v4_name(ip_v4_address, &address_text);
  CHECK_AND_RETURN_SPECIFIC_ERRNO(0 == rv, rv);
  (*result) = "";
  (*result) += address_text;
  (*result) += ":";
  (*result) += port_text;
  return 0;
}

int32 SocketUtils::set_blocking(int sock_fd, bool blocking) {
  CHECK_LE(0, sock_fd) << "Invalid socket.";
  int flags = fcntl(sock_fd, F_GETFL, 0);
  CHECK_AND_RETURN_ERRNO(flags >= 0);

  flags = blocking ? (flags & (~O_NONBLOCK)) : (flags | O_NONBLOCK);
  bool ok = (0 == fcntl(sock_fd, F_SETFL, flags));
  CHECK_AND_RETURN_ERRNO(ok);

#ifdef __MACH__
  int value = 1;
  int result = setsockopt(sock_fd, SOL_SOCKET, SO_NOSIGPIPE, &value,
                          sizeof(value));
  CHECK_AND_RETURN_ERRNO(0 == result);
#endif  // __MACH__

  return 0;
}

int32 SocketUtils::set_nodelay(int sock_fd) {
  int value = 1;
  int result = setsockopt(sock_fd, SOL_TCP, TCP_NODELAY, &value, sizeof(value));
  CHECK_AND_RETURN_ERRNO(0 == result);
  return 0;
}

int32 SocketUtils::set_reuse_address(int sock_fd, bool re_use) {
  int value = re_use ? 1 : 0;
  int result = setsockopt(sock_fd, SOL_SOCKET, SO_REUSEADDR, &value,
                          sizeof(value));
  CHECK_AND_RETURN_ERRNO(0 == result);
  return 0;
}

int32 SocketUtils::set_send_recv_timeout(
    int sock_fd, int timeout_milliseconds) {
  if (timeout_milliseconds < 0) {
    return 0;
  }
  timeval tv = millis_to_timeval(timeout_milliseconds);

  int result = setsockopt(sock_fd, SOL_SOCKET, SO_SNDTIMEO, &tv, sizeof(tv));
  CHECK_AND_RETURN_ERRNO(0 == result);

  result = setsockopt(sock_fd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));
  CHECK_AND_RETURN_ERRNO(0 == result);
  return 0;
}

int32 SocketUtils::get_sock_name(int sock_fd, int32* address, int32* port) {
  sockaddr_in socket_address;
  ZERO_MEMORY(&socket_address, sizeof(socket_address));
  socklen_t socket_address_len = sizeof(socket_address);

  int result = getsockname(
      sock_fd, reinterpret_cast<sockaddr*>(&socket_address),
      &socket_address_len);
  CHECK_AND_RETURN_ERRNO(-1 != result);
  CHECK(socket_address_len == sizeof(socket_address)) << "Unexpected.";

  if (address) {
    (*address) = ntohl(static_cast<int32>(socket_address.sin_addr.s_addr));
  }
  if (port) {
    (*port) = ntohs(socket_address.sin_port);
  }
  return 0;
}

int32 SocketUtils::get_peer_name(int sock_fd, int32* address, int32* port) {
  sockaddr_in socket_address;
  ZERO_MEMORY(&socket_address, sizeof(socket_address));
  socklen_t socket_address_len = sizeof(socket_address);
  int result = getpeername(
      sock_fd, reinterpret_cast<sockaddr*>(&socket_address),
      &socket_address_len);
  CHECK_AND_RETURN_ERRNO(-1 != result);
  CHECK(socket_address_len == sizeof(socket_address)) << "Unexpected.";

  if (address) {
    (*address) = ntohl(static_cast<int32>(socket_address.sin_addr.s_addr));
  }
  if (port) {
    (*port) = ntohs(socket_address.sin_port);
  }
  return 0;
}

int32 SocketUtils::select_wait(int sock_fd, int timeout_milliseconds) {
  if (timeout_milliseconds <= 0) {
    return 0;
  }
  timeval tval = millis_to_timeval(timeout_milliseconds);
  fd_set rset, wset;
  FD_ZERO(&rset);
  FD_SET(sock_fd, &rset);
  wset = rset;

  int result = select(sock_fd + 1, &rset, &wset, NULL, &tval);
  CHECK_AND_RETURN_SPECIFIC_ERRNO(0 != result, ETIMEDOUT);

  bool ok = FD_ISSET(sock_fd, &rset) || FD_ISSET(sock_fd, &wset);
  CHECK_AND_RETURN_SPECIFIC_ERRNO(ok, ETIMEDOUT);

  return 0;
}

int32 SocketUtils::poll_for_read(int sock_fd, int timeout_milliseconds) {
  if (timeout_milliseconds <= 0) {
    return 0;
  }
  pollfd descriptors[1];
  descriptors[0].fd = sock_fd;
  descriptors[0].events = POLLIN;
  int result = poll(descriptors, 1, timeout_milliseconds);
  // Handle interruptions.
  if ((-1 == result) && (EINTR == errno)) {
    return 0;
  }
  // Error in polling.
  CHECK_AND_RETURN_ERRNO(-1 != result);
  // Timed out or socket closed.
  CHECK_AND_RETURN_SPECIFIC_ERRNO(1 == result, ETIMEDOUT);
  if (descriptors[0].revents & POLLIN) {
    return 0;
  }
  CHECK(false) << "Inconsistent state.";
  return 0;
}

int32 SocketUtils::poll_list_for_read(int* sock_fd_list, int list_length,
                                      int* out_sock_fd_list,
                                      int* out_list_length,
                                      int timeout_milliseconds) {
  CHECK_LT(0, timeout_milliseconds);
  cc_shared::scoped_array<pollfd> descriptors(
      new(std::nothrow) pollfd [list_length]);
  ZERO_MEMORY(descriptors.get(), list_length * sizeof(pollfd));
  for (int i = 0; i < list_length; ++i) {
    descriptors[i].fd = sock_fd_list[i];
    descriptors[i].events = POLLIN;
  }
  (*out_list_length) = 0;
  int result = poll(descriptors.get(), list_length, timeout_milliseconds);
  // Handle interruptions.
  if ((-1 == result) && (EINTR == errno)) {
    return 0;
  }
  // Error in polling.
  CHECK_AND_RETURN_ERRNO(-1 != result);
  CHECK_LE(0, result);
  int next = 0;
  for (int i = 0; i < list_length; ++i) {
    if (!(descriptors[i].revents & POLLIN)) {
      continue;
    }
    out_sock_fd_list[next++] = sock_fd_list[i];
  }
  (*out_list_length) = next;
  return 0;
}

int32 SocketUtils::poll_for_write(int sock_fd, int timeout_milliseconds) {
  if (timeout_milliseconds <= 0) {
    return 0;
  }
  pollfd descriptors[1];
  descriptors[0].fd = sock_fd;
  descriptors[0].events = POLLOUT;
  int result = poll(descriptors, 1, timeout_milliseconds);
  // Handle interruptions.
  if ((-1 == result) && (EINTR == errno)) {
    return 0;
  }
  // Error in polling.
  CHECK_AND_RETURN_ERRNO(-1 != result);
  // Timed out or socket closed.
  CHECK_AND_RETURN_SPECIFIC_ERRNO(1 == result, ETIMEDOUT);
  if (descriptors[0].revents & POLLOUT) {
    return 0;
  }
  // Don't know why this happened. We will let caller handle this.
  return 0;
}

int32 SocketUtils::accept_connection(int accepting_sock_fd,
                                     int* connected_sock_fd) {
  sockaddr_in client_address;
  ZERO_MEMORY(&client_address, sizeof(client_address));
  socklen_t client_address_len = sizeof(client_address);
  int sock_fd = accept(accepting_sock_fd,
                       reinterpret_cast<sockaddr*>(&client_address),
                       &client_address_len);
  CHECK_AND_RETURN_ERRNO(0 <= sock_fd);
  CHECK(client_address_len == sizeof(client_address)) << "Unexpected size.";
  (*connected_sock_fd) = sock_fd;
  return 0;
}

int32 SocketUtils::receive_data_from_blocking_socket(
    int sock_fd, char* buffer, int buffer_len, int* bytes_received) {
  CHECK(kInvalidSocket != sock_fd);
  CHECK_LT(0, buffer_len);
  (*bytes_received) = 0;
  while (true) {
    int received_count = recv(sock_fd, buffer, buffer_len, 0);
    if ((received_count < 0) && (EINTR == errno)) {
      continue;
    }
    CHECK_AND_RETURN_ERRNO(received_count >= 0);
    CHECK(received_count <= buffer_len) << "received more bytes than"
                                        << "buffer length.";
    (*bytes_received) = received_count;
    break;
  }
  return 0;
}

int32 SocketUtils::send_data_over_blocking_socket(
    int sock_fd, const char* buffer, int buffer_len) {
  CHECK(kInvalidSocket != sock_fd);
  CHECK(buffer_len >= 0);

  int to_send = buffer_len;
  const char* ptr = buffer;
  while (to_send > 0) {
    int written = send(sock_fd, ptr, to_send, MSG_NOSIGNAL);
    if (written < 0 && errno == EINTR) {
      written = 0;
    }
    if (written < 0 && errno == ENOBUFS) {
      written = 0;
    }
    CHECK_AND_RETURN_ERRNO(written >= 0);
    CHECK(written <= to_send) << "Couldn't have sent more bytes than what was"
                              << "available";
    ptr += written;
    to_send -= written;
  }
  return 0;
}

int32 SocketUtils::receive_data_from_non_blocking_socket(
    int sock_fd, char* buffer, int buffer_len, int* bytes_received) {
  CHECK(kInvalidSocket != sock_fd);
  CHECK_LT(0, buffer_len);
  (*bytes_received) = 0;
  while (true) {
    int received_count = recv(sock_fd, buffer, buffer_len, 0);
    if (received_count < 0) {
      if (EINTR == errno) {
        continue;
      }
      CHECK_AND_RETURN_ERRNO(false);
    }
    CHECK_AND_RETURN_ERRNO(received_count >= 0);
    CHECK(received_count <= buffer_len) << "received more bytes than"
                                        << "buffer length.";
    (*bytes_received) = received_count;
    break;
  }
  return 0;
}

// TODO: Add mechanism to poll for read and write using many sockets in
// parallel. Use this mechanism for reads & writes.
int32 SocketUtils::send_data_over_non_blocking_socket(
    int sock_fd, const char* buffer, int buffer_len) {
  static const int kWaitMillis = 1;
  CHECK(kInvalidSocket != sock_fd);
  CHECK(buffer_len >= 0);

  int to_send = buffer_len;
  const char* ptr = buffer;
  bool do_wait = false;
  while (to_send > 0) {
    if (do_wait) {
      (void) poll_for_write(sock_fd, kWaitMillis);
      do_wait = false;
    }
    int written = send(sock_fd, ptr, to_send, MSG_NOSIGNAL);
    if (written < 0 && errno == EAGAIN) {
      do_wait = true;
      continue;
    }
    if (written < 0 && errno == EINTR) {
      written = 0;
    }
    if (written < 0 && errno == ENOBUFS) {
      written = 0;
    }
    CHECK_AND_RETURN_ERRNO(written >= 0);
    CHECK(written <= to_send) << "Couldn't have sent more bytes than what was"
                              << "available";
    ptr += written;
    to_send -= written;
  }
  return 0;
}

#ifdef __gnu_linux__
int32 SocketUtils::create_epoll(int* epoll_fd) {
  int fd = epoll_create(1);
  CHECK_AND_RETURN_ERRNO(fd >= 0);
  (*epoll_fd) = fd;
  return 0;
}

int32 SocketUtils::ctl_epoll(int epoll_fd, int target_fd, int64 callback_handle,
                             int operation, int events) {
  epoll_event event;
  ZERO_MEMORY(&event, sizeof(event));
  event.data.ptr = reinterpret_cast<void*>(callback_handle);
  event.events = events;
  int rv = epoll_ctl(epoll_fd, operation, target_fd, &event);
  CHECK_AND_RETURN_ERRNO(0 == rv);
  return 0;
}

int32 SocketUtils::wait_epoll(int epoll_fd, epoll_event* events, int max_events,
                              int timeout_millis, int* event_count) {
  int rv = epoll_wait(epoll_fd, events, max_events, timeout_millis);
  CHECK_AND_RETURN_ERRNO(0 <= rv);
  (*event_count) = rv;
  return 0;
}

#endif  // __gnu_linux__

}  // namespace cc_net
