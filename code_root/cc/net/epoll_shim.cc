/*Implementation of epoll shim module.*/
//
// Enable for miscellaneous logging.
// #define CC_TRACE_ENABLED
//

#include "cc/net/epoll_shim.h"
#include "cc/net/socket_utils.h"


#ifndef USE_EPOLL
#include "cc/shared/scoped_array.h"
#include <boost/bind.hpp>
using cc_shared::Mutex;
using cc_shared::ScopedMutex;
using cc_shared::scoped_array;
#endif  // USE_EPOLL

namespace cc_net {

#ifdef USE_EPOLL

EpollShim::EpollShim(EpollServer* epoll_server, SERVER_UPCALL upcall)
    : epoll_server_(epoll_server), upcall_(upcall),
      epoll_fd_(kInvalidSocket) {
  int result = SocketUtils::create_epoll(&epoll_fd_);
  CHECK_EQ(0, result) << "Could not create epoll fd." << strerror(result);
  TRACE_FILE_EVENT("fd:" << epoll_fd_ << " := epoll_fd_ ");
  TRACE_FILE_EVENT("Using epoll for polling (efficient).");
}

EpollShim::~EpollShim() {
  int32 result = SocketUtils::close_socket(epoll_fd_);
  CHECK_EQ(0, result);
}

void EpollShim::process_next_batch() {
  static const int kErrorWaitTimeoutMicros = 10;
  static const int kWaitTimeoutMillis = 5;
  static const int kMaxEvents = 32;
  epoll_event events[kMaxEvents];

  int event_count = 0;
  int32 result = SocketUtils::wait_epoll(
      epoll_fd_, events, kMaxEvents, kWaitTimeoutMillis, &event_count);
  if (0 != result) {
    TRACE_FILE_EVENT("wait_epoll returned " << result);
    usleep(kErrorWaitTimeoutMicros);
    return;
  }
  for (int i = 0; i < event_count; ++i) {
    if (!(events[i].events & EPOLLIN)) {
      continue;
    }
    int64 connection_handle = reinterpret_cast<int64>(events[i].data.ptr);
    upcall_(epoll_server_, connection_handle);
  }
}

int32 EpollShim::add_one_shot_callback(int64 connection_handle, int target_fd) {
  TRACE_FILE_EVENT("fd:" << target_fd << " add_one_shot_callback");
  return update_event(target_fd, connection_handle, EPOLL_CTL_ADD);
}

int32 EpollShim::reapply_one_shot_callback(int64 connection_handle,
                                           int target_fd) {
  TRACE_FILE_EVENT("fd:" << target_fd << " reapply_one_shot_callback");
  return update_event(target_fd, connection_handle, EPOLL_CTL_MOD);
}

int32 EpollShim::delete_one_shot_callback(int64 connection_handle,
                                          int target_fd) {
  TRACE_FILE_EVENT("fd:" << target_fd << " delete_one_shot_callback");
  return update_event(target_fd, 0, EPOLL_CTL_DEL);
}

void EpollShim::try_delete_one_shot_callback(int64 connection_handle,
                                             int target_fd) {
  // This is a no-op for Linux. Kernel handles removal of sockets from epoll
  // queue if the descriptor is closed.
}

int32 EpollShim::update_event(int target_fd, int64 connection_handle,
                              int operation) {
  static const int kAllEvents = EPOLLIN | EPOLLET | EPOLLONESHOT;
  static const int kNoEvents = 0;
  return SocketUtils::ctl_epoll(
      epoll_fd_, target_fd, connection_handle, operation,
      (EPOLL_CTL_DEL == operation) ? kNoEvents : kAllEvents);
}

#else
// Implementation using poll.

EpollShim::EpollShim(EpollServer* epoll_server, SERVER_UPCALL upcall)
    : epoll_server_(epoll_server), upcall_(upcall) {
  TRACE_FILE_EVENT("Using poll for polling (inefficient).");
}

EpollShim::~EpollShim() {
  CHECK(lookup_.begin() == lookup_.end());
}

void EpollShim::process_next_batch() {
  static const int kErrorWaitTimeoutMicros = 100;
  static const int kWaitTimeoutMillis = 1;
  scoped_array<int> sock_fd_list(NULL);
  scoped_array<int> out_sock_fd_list(NULL);
  int list_length = 0;
  int returned_list_length = 0;
  {
    ScopedMutex scoped(&lock_);
    list_length = static_cast<int>(lookup_.size());
    sock_fd_list.replace(new(std::nothrow) int [list_length]);
    out_sock_fd_list.replace(new(std::nothrow) int [list_length]);
    boost::unordered_map<int, int64>::iterator iter;
    int next = 0;
    for (iter = lookup_.begin(); iter != lookup_.end(); ++iter) {
      sock_fd_list[next++] = iter->first;
    }
  }
  int32 result = SocketUtils::poll_list_for_read(
      sock_fd_list.get(), list_length, out_sock_fd_list.get(),
      &returned_list_length, kWaitTimeoutMillis);
  if (result != 0) {
    usleep(kErrorWaitTimeoutMicros);
    return;
  }
  for (int i = 0; i < returned_list_length; ++i) {
    int64 connection_handle = -1;
    bool found = false;
    // Even though many threads could have been polling and could have
    // received the same items, lets not share the same socket out to more
    // than one waiting thread.
    {
      ScopedMutex scoped(&lock_);
      int sock_fd = out_sock_fd_list[i];
      if (lookup_.find(sock_fd) != lookup_.end()) {
        connection_handle = lookup_[sock_fd];
        lookup_.erase(sock_fd);
        found = true;
      }
    }
    if (found) {
      upcall_(epoll_server_, connection_handle);
    }
  }
}

int32 EpollShim::add_one_shot_callback(int64 connection_handle, int target_fd) {
  TRACE_FILE_EVENT("fd:" << target_fd << " add_one_shot_callback");
  ScopedMutex scoped(&lock_);
  boost::unordered_map<int, int64>::iterator iter;
  iter = lookup_.find(target_fd);
  if (lookup_.end() != iter) {
    int64 actual_connection_handle = iter->second;
    CHECK_NE(actual_connection_handle, connection_handle);
  }
  lookup_[target_fd] = connection_handle;
  return 0;
}

int32 EpollShim::reapply_one_shot_callback(int64 connection_handle,
                                           int target_fd) {
  TRACE_FILE_EVENT("fd:" << target_fd << " reapply_one_shot_callback");
  return add_one_shot_callback(connection_handle, target_fd);
}

int32 EpollShim::delete_one_shot_callback(int64 connection_handle,
                                          int target_fd) {
  TRACE_FILE_EVENT("fd:" << target_fd << " delete_one_shot_callback");
  ScopedMutex scoped(&lock_);
  boost::unordered_map<int, int64>::iterator iter;
  iter = lookup_.find(target_fd);
  if (lookup_.end() == iter) {
    return 0;
  }
  int64 actual_connection_handle = iter->second;
  if (connection_handle != actual_connection_handle) {
    // Must have been re-added in a separate thread.
    return 0;
  }
  lookup_.erase(target_fd);
  return 0;
}

void EpollShim::try_delete_one_shot_callback(int64 connection_handle,
                                             int target_fd) {
  TRACE_FILE_EVENT("fd:" << target_fd << " try_delete_one_shot_callback");
  delete_one_shot_callback(connection_handle, target_fd);
  return;
}

#endif   // USE_EPOLL

}  // cc_net
