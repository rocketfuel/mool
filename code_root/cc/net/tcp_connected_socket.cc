/*Implementation of string builder module.*/
#include "cc/net/tcp_connected_socket.h"
#include "cc/net/socket_utils.h"
#include <boost/atomic.hpp>

using boost::atomic;
using std::string;

#define LOG_TCP_SOCKET 0

#if LOG_TCP_SOCKET
#define LOG_TCP_SOCKET_EVENT(_x) {    \
  int ee = errno;                     \
  LOG(INFO) << _x;                    \
  errno = ee;                         \
}
#else
#define LOG_TCP_SOCKET_EVENT(_x)
#endif

namespace cc_net {

namespace {

void close_socket_impl(int32* native_socket) {
  int result = SocketUtils::close_socket(*native_socket);
  CHECK_EQ(0, result);
  (*native_socket) = kInvalidSocket;
}

}  // namespace

TcpConnectedSocket::TcpConnectedSocket()
    : native_socket_(kInvalidSocket), local_address_(0), local_port_(0),
      remote_address_(0), remote_port_(0), is_blocking_(false) {
}

TcpConnectedSocket::~TcpConnectedSocket() {
  close_socket();
}

void TcpConnectedSocket::close_socket() {
  if (kInvalidSocket != native_socket_) {
    LOG_TCP_SOCKET_EVENT("Closing socket for " << " local_port: "
                         << local_port_);
  }
  close_socket_impl(&native_socket_);
}

int32 TcpConnectedSocket::load_address_port_info() {
  int result = SocketUtils::get_sock_name(native_socket_, &local_address_,
                                          &local_port_);
  if (result) return result;
  return SocketUtils::get_peer_name(native_socket_, &remote_address_,
                                    &remote_port_);
}

int32 TcpConnectedSocket::set_blocking(int timeout_milliseconds) {
  bool blocking = (timeout_milliseconds > 0);
  int result = SocketUtils::set_blocking(native_socket_, blocking);
  if (result) return result;
  is_blocking_ = blocking;
  timeout_milliseconds = blocking ? timeout_milliseconds : 0;
  result = SocketUtils::set_send_recv_timeout(native_socket_,
                                              timeout_milliseconds);
  if (result) return result;
  return 0;
}

int32 TcpConnectedSocket::initialize(
    const string& host, const string& port, int timeout_milliseconds) {
  CHECK_EQ(kInvalidSocket, native_socket_) << "Already initialized.";
  int result = 0;
  do {
    result = SocketUtils::initialize_stream_socket(
        host.c_str(), port.c_str(), false, true, false, timeout_milliseconds,
        &native_socket_);
    if (result) break;

    result = load_address_port_info();
    if (result) break;

    result = set_blocking(timeout_milliseconds);
    if (result) break;
  } while (false);
  // Error cases handled by destructor.
  if (result) {
    LOG_TCP_SOCKET_EVENT("Could not initialize connected socket for " << host
                         << ":" << port);
  } else {
    LOG_TCP_SOCKET_EVENT("Initialized connected socket for " << host
                         << ":" << port << " local_port: " << local_port_);
  }
  return result;
}

string TcpConnectedSocket::get_local_address_port() {
  string rv;
  int result = SocketUtils::get_address_port_text(local_address_, local_port_,
                                                  &rv);
  CHECK_EQ(0, result);
  return rv;
}

string TcpConnectedSocket::get_remote_address_port() {
  string rv;
  int result = SocketUtils::get_address_port_text(remote_address_, remote_port_,
                                                  &rv);
  CHECK_EQ(0, result);
  return rv;
}

int32 TcpConnectedSocket::send_blocking(const char* buffer, int buffer_len) {
  CHECK(is_blocking_);
  return SocketUtils::send_data_over_blocking_socket(
      native_socket_, buffer, buffer_len);
}

int32 TcpConnectedSocket::receive_blocking(
    char* buffer, int buffer_len, int* bytes_received) {
  CHECK(is_blocking_);
  return SocketUtils::receive_data_from_blocking_socket(
      native_socket_, buffer, buffer_len, bytes_received);
}

}  // cc_net
