/*Unit tests for socket epoll.*/
// #define CC_TRACE_ENABLED
#include "cc/net/epoll_server.h"
#include "cc/net/socket_utils.h"
#include "cc/shared/scoped_ptr.h"
#include "gtest/gtest.h"

#include <boost/atomic.hpp>
#include <boost/bind.hpp>
#include <boost/lexical_cast.hpp>
#include <boost/unordered_map.hpp>
#include <boost/thread.hpp>

using std::string;

namespace cc_net {

namespace {

string receive_server_response(int sock_fd, int buffer_byte_count) {
  static const int kBufferLen = 100;
  char receiver[kBufferLen];
  CHECK_LT(0, buffer_byte_count);
  string answer;
  int remaining_bytes = buffer_byte_count;
  while (remaining_bytes > 0) {
    int bytes_received = 0;
    int result = SocketUtils::receive_data_from_blocking_socket(
        sock_fd, receiver, std::min(remaining_bytes, kBufferLen - 1),
        &bytes_received);
    if (0 != result) {
      return "";
    }
    CHECK_LE(0, bytes_received);
    CHECK_LE(bytes_received, remaining_bytes);
    if (0 == bytes_received) {
      return answer;
    }
    remaining_bytes -= bytes_received;
    receiver[bytes_received] = 0;
    answer += receiver;
  }
  return answer;
}

}  // namespace

class EpollServerTest : public testing::Test {
 protected:
  static const char kMessage[];
  static const int kMessageLen;

  class ConnectionHandler : public EpollServer::EpollConnectionHandler {
   public:
    ConnectionHandler()
        : offset_(kMessageLen - 1), epoll_server_test_(NULL),
          epoll_server_(NULL), connection_handle_(-1) {
    }

    virtual ~ConnectionHandler() {
    }

    void set_parent(EpollServerTest* epoll_server_test) {
      epoll_server_test_ = epoll_server_test;
      epoll_server_test_->register_server_connection();
    }

    virtual void set_context(int64 connection_handle,
                             EpollServer* epoll_server) {
      epoll_server_ = epoll_server;
      connection_handle_ = connection_handle;
    }

    virtual void handle_buffer(const char* buffer, int byte_count) {
      CHECK_LT(0, byte_count);
      TRACE_FILE_EVENT("Received " << byte_count << " bytes for "
                       << connection_handle_);
      for (int i = 0; i < byte_count; ++i) {
        offset_ = (offset_ + 1) % kMessageLen;
        CHECK_EQ(kMessage[offset_], buffer[i]);
      }
      if (offset_ == (kMessageLen - 1)) {
        TRACE_FILE_EVENT("Server sending echo response for "
                         << connection_handle_);
        epoll_server_->send_blocking(connection_handle_, kMessage, kMessageLen);
      }
    }

   private:
    // How many bytes of the test message we have seen so far.
    int offset_;
    EpollServerTest* epoll_server_test_;
    EpollServer* epoll_server_;
    int64 connection_handle_;
    DISALLOW_COPY_AND_ASSIGN(ConnectionHandler);
  };

  cc_shared::scoped_ptr<EpollServer> epoll_server_;
  boost::atomic<int64> server_connected_;
  boost::atomic<int64> client_connected_;
  boost::atomic<int64> client_send_count_;
  boost::atomic<int64> client_received_count_;
  HandlerGetter<EpollServerTest, ConnectionHandler> getter_;

  EpollServerTest()
      : server_connected_(0), client_connected_(0), client_send_count_(0),
        client_received_count_(0), getter_(this) {
  }

 public:
  void register_server_connection() {
    ++server_connected_;
  }

  void do_client_transactions(int sock_fd, int transaction_count) {
    int32 result = 0;
    for (int i = 0; i < transaction_count; ++i) {
      TRACE_FILE_EVENT("Client sending echo request.");
      result = SocketUtils::send_data_over_blocking_socket(
          sock_fd, kMessage, kMessageLen);
      if (result) {
        TRACE_FILE_EVENT("Client send error '" << strerror(result) << "'");
        break;
      }
      ++client_send_count_;
      string response = receive_server_response(sock_fd, kMessageLen);
      if (0 != strcmp(kMessage, response.c_str())) {
        TRACE_FILE_EVENT("Client received mismatch '" << response << "'");
        break;
      }
      TRACE_FILE_EVENT("Client received correct response.");
      ++client_received_count_;
    }
  }

  void client_main(int client_index, int max_iterations,
                   int transaction_count, const char* host, const char* port) {
    static const int kClientSocketTimeoutMillis = 2000;
    static const int kIntraIterationWaitMicros = 5000;
    int32 result = 0;
    for (int i = 0; i < max_iterations; ++i) {
      usleep(kIntraIterationWaitMicros);
      int sock_fd = kInvalidSocket;
      result = SocketUtils::initialize_stream_socket(
          host, port, false, false, false, kClientSocketTimeoutMillis,
          &sock_fd);
      if (result) {
        TRACE_FILE_EVENT("Client could not connect: " << strerror(result));
        continue;
      }
      CHECK_NE(kInvalidSocket, sock_fd);
      TRACE_FILE_EVENT("Client (" << client_index << ") connected.");
      ++client_connected_;
      result = SocketUtils::set_blocking(sock_fd, true);
      if (0 == result) {
        do_client_transactions(sock_fd, transaction_count);
      }
      TRACE_FILE_EVENT("Client (" << client_index << ") disconnecting.");
      SocketUtils::close_socket(sock_fd);
    }
  }
};

const char EpollServerTest::kMessage[] = "To every action there is"
                                         " an equal and opposite reaction.";
const int EpollServerTest::kMessageLen = ARRAY_SIZE(EpollServerTest::kMessage);

TEST_F(EpollServerTest, test_end_to_end) {
  static const char* kHost = "127.0.0.1";
  static const char* kPort = "0";
  static const int kMicrosPerSecond = 1000000;

  bool stress_mode = !!getenv("TCP_TEST_E2E_MODE");
  int server_threads = stress_mode ? 15 : 3;
  int client_threads = stress_mode ? 6 : 2;
  int max_iterations = stress_mode ? 75 : 5;
  int transaction_count = stress_mode ? 1500 : 500;

  CHECK_EQ(NULL, epoll_server_.get());
  epoll_server_.replace(
      new(std::nothrow) EpollServer(kHost, kPort, &getter_, server_threads));
  string port_text = boost::lexical_cast<string>(
      epoll_server_->get_actual_port());

  boost::thread_group client_thread_group;
  for (int i = 0; i < client_threads; ++i) {
    client_thread_group.create_thread(
        boost::bind(&EpollServerTest::client_main, this, i, max_iterations,
                    transaction_count, kHost, port_text.c_str()));
  }
  client_thread_group.join_all();
  // Give the server some time to cool down pending connections.
  usleep(kMicrosPerSecond / 2);
  epoll_server_.reset();
  int64 max_messages = (
      static_cast<int64>(transaction_count) * client_connected_);
  LOG(INFO) << "Stress mode: " << stress_mode;
  LOG(INFO) << "Client connection count: " << client_connected_;
  LOG(INFO) << "Server connection count: " << server_connected_;

  LOG(INFO) << "Client send count    : " << client_send_count_ << " (out of "
            << max_messages << ")";
  LOG(INFO) << "Client received count: " << client_received_count_;

  // Some light-weight checks to catch big errors only.
  EXPECT_TRUE(client_connected_ < 2.0 * server_connected_);
  EXPECT_TRUE(client_connected_ > (2 * client_threads));
  EXPECT_TRUE(client_send_count_ > 0.5 * max_messages);
  EXPECT_TRUE(client_received_count_ > 0.8 * client_send_count_);
}

}  // namespace cc_net
