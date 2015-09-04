/*Implementation of epoll server module.*/
//
// Enable for miscellaneous logging.
// #define CC_TRACE_ENABLED
//
// Enable for API events (in both directions).
// #define TRACE_API_EVENTS
//

#include "cc/net/epoll_server.h"
#include "cc/net/socket_utils.h"
#include "cc/shared/scoped_array.h"

#include <vector>

#include <boost/bind.hpp>
#include <boost/thread/thread.hpp>

using cc_shared::Mutex;
using cc_shared::ScopedMutex;
using cc_shared::scoped_array;
using std::vector;

namespace cc_net {

namespace {

int32 close_file_descriptor(int descriptor) {
  TRACE_FILE_EVENT("fd:" << descriptor << " " << __FUNCTION__);
  return SocketUtils::close_socket(descriptor);
}

void server_upcall(EpollServer* epoll_server, int64 connection_handle) {
  epoll_server->handle_upcall(connection_handle);
}

}  // namespace

EpollServer::EpollServer(
  const char* host, const char* port,
  EpollServer::EpollConnectionHandlerFactory* getter, int wait_thread_count)
    : acceptor_handle_(-1),
      acceptor_fd_(kInvalidSocket),
      actual_port_(0),
      getter_(getter),
      epoll_shim_(NULL),
      wait_threads_(new(std::nothrow) boost::thread_group()),
      wait_thread_count_(wait_thread_count),
      handle_seed_(-1) {
  TRACE_API_EVENT("--> Start EpollServer: " << host << ":" << port << " with "
                  << wait_thread_count << " threads");
  int32 result = 0;

  // Make a non-blocking acceptor socket.
  result = SocketUtils::initialize_stream_socket(host, port, true, false,
                                                 true, -1, &acceptor_fd_);
  CHECK_EQ(0, result) << "Could not initialize stream socket."
                      << strerror(result);
  acceptor_handle_ = get_new_connection_handle(acceptor_fd_);
  TRACE_FILE_EVENT("fd:" << acceptor_fd_ << " := acceptor_fd_ ");

  CHECK_EQ(NULL, epoll_shim_.get());
  epoll_shim_.replace(new(std::nothrow) EpollShim(this, server_upcall));

  result = SocketUtils::get_sock_name(acceptor_fd_, NULL, &actual_port_);
  CHECK_EQ(0, result) << "Could not get sock name." << strerror(result);

  result = epoll_shim_->add_one_shot_callback(acceptor_handle_, acceptor_fd_);
  CHECK_EQ(0, result) << "Could not add acceptor callback." << strerror(result);

  for (int i = 0; i < wait_thread_count_; ++i) {
    wait_threads_->create_thread(boost::bind(&EpollServer::wait_worker, this));
  }
}

int64 EpollServer::get_new_connection_handle(int descriptor) {
  ScopedMutex scoped(&lock_);
  int64 connection_handle = ++handle_seed_;
  handle_to_fd_lookup_[connection_handle] = descriptor;
  TRACE_FILE_EVENT("handle_to_fd_lookup_[" << connection_handle << "] := "
                   << descriptor);
  return connection_handle;
}

EpollServer::~EpollServer() {
  TRACE_API_EVENT("--> Stopping EpollServer");
  wait_threads_->interrupt_all();
  wait_threads_->join_all();

  boost::unordered_map<int64, int>::iterator iter;
  vector<int64> to_be_completed;
  for (iter = handle_to_fd_lookup_.begin();
       iter != handle_to_fd_lookup_.end(); ++iter) {
    int64 connection_handle = iter->first;
    if (connection_handle == acceptor_handle_) {
      continue;
    }
    to_be_completed.push_back(connection_handle);
  }

  for (int i = 0; i < VSIZE(to_be_completed); ++i) {
    complete_connection_socket(to_be_completed[i]);
  }
  CHECK_EQ(0, handler_lookup_.size());
  CHECK_EQ(0, handler_refcount_.size());

  int32 result = epoll_shim_->delete_one_shot_callback(
      acceptor_handle_, acceptor_fd_);
  CHECK_EQ(0, result);

  epoll_shim_.reset();

  result = close_file_descriptor(acceptor_fd_);
  CHECK_EQ(0, result);
}

void EpollServer::complete_connection_socket(int64 connection_handle) {
  int sock_fd = kInvalidSocket;
  do {
      ScopedMutex scoped(&lock_);
      boost::unordered_map<int64, int>::iterator iter
          = handle_to_fd_lookup_.find(connection_handle);
      if (iter == handle_to_fd_lookup_.end()) {
        break;
      }
      sock_fd = iter->second;
      handle_to_fd_lookup_.erase(iter);
  } while (false);

  if (kInvalidSocket == sock_fd) {
    return;
  }
  TRACE_FILE_EVENT("fd:" << sock_fd << " completed");
  // TODO: Figure out if it is a good idea to do this in a different thread.
  epoll_shim_->try_delete_one_shot_callback(connection_handle, sock_fd);
  upcall_connection_closed(connection_handle);
  int32 result = close_file_descriptor(sock_fd);
  if (result) {
    TRACE_FILE_EVENT("Socket close failed, ignoring: " << strerror(result));
  }
}

void EpollServer::close_connection(int64 connection_handle) {
  TRACE_API_EVENT("--> close_connection: " << connection_handle);
  TRACE_FILE_EVENT("Received close_connection for " << connection_handle);
  complete_connection_socket(connection_handle);
}

void EpollServer::send_blocking(int64 connection_handle, const char* buffer,
                                int byte_count) {
  // Send traces are really verbose, enable if needed.
  // TRACE_API_EVENT("--> send_blocking: " << connection_handle << " "
  //                 << byte_count << " bytes");
  int sock_fd = kInvalidSocket;
  {
    ScopedMutex scoped(&lock_);
    sock_fd = handle_to_fd_lookup_[connection_handle];
  }
  if (kInvalidSocket == sock_fd) {
    return;
  }
  int32 result = SocketUtils::send_data_over_non_blocking_socket(
      sock_fd, buffer, byte_count);
  if (result) {
    TRACE_FILE_EVENT("fd:" << sock_fd << " " << __FUNCTION__
                     << " " << byte_count << " bytes failed with '"
                     << strerror(result) << "'");
    complete_connection_socket(connection_handle);
  } else {
    TRACE_FILE_EVENT("fd:" << sock_fd << " " << __FUNCTION__
                     << " " << byte_count << " bytes");
  }
  // TRACE_API_EVENT("<-- send_blocking: " << connection_handle << " "
  //                 << byte_count << " bytes");
}

void EpollServer::do_connection_upcall(int64 connection_handle) {
  // We are using edge-triggering, so we must read the entire payload right
  // away.
  static const int kReceiverSize = 1024;
  char receiver[kReceiverSize];
  int result = 0;
  int bytes_received = 0;
  bool close_socket = false;
  int sock_fd = kInvalidSocket;
  {
    ScopedMutex scoped(&lock_);
    sock_fd = handle_to_fd_lookup_[connection_handle];
  }

  while (true) {
    bytes_received = 0;
    result = SocketUtils::receive_data_from_non_blocking_socket(
        sock_fd, receiver, kReceiverSize, &bytes_received);
    if (EAGAIN == result) {
      CHECK_EQ(0, bytes_received);
      break;
    }
    if (0 == bytes_received) {
      close_socket = true;
      break;
    }
    CHECK_LT(0, bytes_received);
    CHECK_LE(bytes_received, kReceiverSize);

    TRACE_FILE_EVENT("fd:" << sock_fd << " receiving " << bytes_received
                     << " bytes");
    upcall_handle_buffer(connection_handle, receiver, bytes_received);
  }

  if (!close_socket) {
    result = epoll_shim_->reapply_one_shot_callback(connection_handle, sock_fd);
    if (result) {
      TRACE_FILE_EVENT("Could not reapply callback for " << sock_fd);
      close_socket = true;
    }
  }

  if (close_socket) {
    TRACE_FILE_EVENT("Connection closed by peer for " << sock_fd);
    complete_connection_socket(connection_handle);
  }
}

void EpollServer::do_connection_accept() {
  int sock_fd = kInvalidSocket;
  int32 result = 0;

  do {
    result = SocketUtils::accept_connection(acceptor_fd_, &sock_fd);
    if (0 != result) {
      // There are known scenarios when acceptor socket can be woken up without
      // the connection eventually getting ready to be accepted. This is rare,
      // but normal.
      result = 0;
      break;
    }
    CHECK_NE(kInvalidSocket, sock_fd);

    TRACE_FILE_EVENT("fd:" << sock_fd << " new connection.");
    result = SocketUtils::set_blocking(sock_fd, false);
    if (result) {
      TRACE_FILE_EVENT("Error setting to non-blocking for " << sock_fd
                       << ": with " << strerror(result));
      break;
    }

    result = SocketUtils::set_nodelay(sock_fd);
    if (result) {
      TRACE_FILE_EVENT("Error setting TCP_NODELAY for " << sock_fd
                       << ": with " << strerror(result));
      break;
    }

    int64 connection_handle = get_new_connection_handle(sock_fd);

    TRACE_FILE_EVENT("fd:" << sock_fd << " Connection started");
    upcall_connection_started(connection_handle);
    int32 sock_fd_saved = sock_fd;
    sock_fd = kInvalidSocket;

    // It is important to add this callback after sending the upcall for
    // starting connection. Otherwise callback can get connection close before
    // connection start.
    result = epoll_shim_->add_one_shot_callback(connection_handle,
                                                sock_fd_saved);
    if (result) {
      complete_connection_socket(connection_handle);
    }
  } while (false);

  if (sock_fd != kInvalidSocket) {
    result = close_file_descriptor(sock_fd);
    if (result) {
      TRACE_FILE_EVENT("Failed to close socket at " << sock_fd << ": with "
                       << strerror(result));
    }
  }

  result = epoll_shim_->reapply_one_shot_callback(acceptor_handle_,
                                                  acceptor_fd_);
  CHECK_EQ(0, result) << "Accept has stopped working, shutting down.";
}

void EpollServer::handle_upcall(int64 connection_handle) {
  TRACE_FILE_EVENT("Upcall for connection handle " << connection_handle);
  if (connection_handle == acceptor_handle_) {
    do_connection_accept();
  } else {
    do_connection_upcall(connection_handle);
  }
}

void EpollServer::wait_worker() {
  while (!boost::this_thread::interruption_requested()) {
    epoll_shim_->process_next_batch();
  }
}

void EpollServer::handler_ref(int64 connection_handle) {
  ScopedMutex scoped(&lock_);
  handler_refcount_[connection_handle] += 1;
  // Packet upcall path is expected to be serialized.
  CHECK_LE(handler_refcount_[connection_handle], 2);
}

void EpollServer::handler_deref(int64 connection_handle) {
  ScopedMutex scoped(&lock_);
  handler_refcount_[connection_handle] -= 1;
  if (0 == handler_refcount_[connection_handle]) {
    TRACE_API_EVENT("<-- connection closed " << connection_handle);
    handler_lookup_[connection_handle]->finalize();
    handler_lookup_.erase(connection_handle);
    handler_refcount_.erase(connection_handle);
  }
}

void EpollServer::upcall_connection_started(int64 connection_handle) {
  ScopedMutex scoped(&lock_);
  CHECK(handler_lookup_.end() == handler_lookup_.find(connection_handle));
  TRACE_API_EVENT("<-- connection_started() for " << connection_handle);
  EpollConnectionHandler* handler = getter_->get();
  if (!handler) {
    TRACE_FILE_EVENT("Could not generate handler for " << connection_handle);
    TRACE_API_EVENT("get() failed for " << connection_handle);
    return;
  }
  handler->set_context(connection_handle, this);
  handler_lookup_[connection_handle] = handler;
  handler_refcount_[connection_handle] = 0;
  handler_ref(connection_handle);
}

void EpollServer::upcall_connection_closed(int64 connection_handle) {
  ScopedMutex scoped(&lock_);
  // Connection close packet and data packet can come out of order as we have
  // multiple threads waiting on the epoll event. It is also possible that the
  // connection could not be generated because of low-memory conditions.
  if (handler_lookup_.end() == handler_lookup_.find(connection_handle)) {
    TRACE_FILE_EVENT("Missing handler for " << connection_handle);
    return;
  }
  handler_deref(connection_handle);
}

void EpollServer::upcall_handle_buffer(
  int64 connection_handle, const char* buffer, int byte_count) {
  EpollConnectionHandler* epoll_connection_handler = NULL;
  // Scoping block.
  {
    ScopedMutex scoped(&lock_);
    CHECK_LT(0, byte_count);
    // Connection close packet and data packet can come out of order as we have
    // multiple threads waiting on the epoll event. It is also possible that the
    // connection could not be generated because of low-memory conditions.
    if (handler_lookup_.end() == handler_lookup_.find(connection_handle)) {
      TRACE_FILE_EVENT("Missing handler for " << connection_handle);
      TRACE_API_EVENT("Missing handler for " << connection_handle);
      close_connection(connection_handle);
      return;
    }
    TRACE_FILE_EVENT("Received " << byte_count << " bytes for "
                     << connection_handle);
    handler_ref(connection_handle);
    epoll_connection_handler = handler_lookup_[connection_handle];
  }
  // Receive traces are really verbose, enable if needed.
  // TRACE_API_EVENT("<-- received: " << connection_handle << " "
  //                 << byte_count << " bytes");
  if (epoll_connection_handler) {
    epoll_connection_handler->handle_buffer(buffer, byte_count);
  }
  handler_deref(connection_handle);
}

}  // cc_net
