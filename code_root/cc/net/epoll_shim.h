/* Header file for epoll shim.

It provides the real epoll interface on Linux.
It provides a mock epoll interface (over poll) on Mac OS.
*/
#ifndef __CC_NET_EPOLL_SHIM__
#define __CC_NET_EPOLL_SHIM__

#include "cc/shared/common.h"


#undef USE_EPOLL
#ifdef __gnu_linux__
#define USE_EPOLL
#endif  // __gnu_linux__

#ifndef USE_EPOLL
#include "cc/shared/mutex.h"
#include <boost/unordered_map.hpp>
#endif  // USE_EPOLL

namespace cc_net {

// Forward declaration.
class EpollServer;

typedef void (*SERVER_UPCALL)(EpollServer* epoll_server,
                              int64 connection_handle);

class EpollShim {
 public:
  EpollShim(EpollServer* epoll_server, SERVER_UPCALL upcall);

  ~EpollShim();

  void process_next_batch();

  int32 add_one_shot_callback(int64 connection_handle, int target_fd);

  int32 reapply_one_shot_callback(int64 connection_handle, int target_fd);

  int32 delete_one_shot_callback(int64 connection_handle, int target_fd);

  void try_delete_one_shot_callback(int64 connection_handle, int target_fd);

 private:
  EpollServer* epoll_server_;
  SERVER_UPCALL upcall_;

#ifdef USE_EPOLL
  int epoll_fd_;
  int32 update_event(int target_fd, int64 connection_handle, int operation);

#else
  cc_shared::Mutex lock_;
  boost::unordered_map<int, int64> lookup_;

#endif  // USE_EPOLL

  DISALLOW_COPY_AND_ASSIGN(EpollShim);
};

}  // cc_net

#endif  // __CC_NET_EPOLL_SHIM__
