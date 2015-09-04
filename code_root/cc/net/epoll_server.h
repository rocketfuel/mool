/* Header file for Tcp Server using epoll based reads.

The epoll interface is automatically available on Linux operating systems.
However, a significant amount of our development work happens on Mac OS.

One of our goals is to have a codebase that can be built and tested on both
Mac OS and Linux. However, the code only needs to be performant on our Linux
cluster machines.

Current module is a layer imitating the Linux epoll mechanism. On Linux, this
module uses epoll directly in edge triggered mode. On Mac OS this module uses
polling internally.

*/
#ifndef __CC_NET_EPOLL_SERVER__
#define __CC_NET_EPOLL_SERVER__

#include "cc/net/epoll_shim.h"
#include "cc/shared/common.h"
#include "cc/shared/mutex.h"
#include "cc/shared/scoped_ptr.h"

#include <boost/unordered_map.hpp>

// Forward declarations.
namespace boost {
class thread_group;
}  // boost

namespace cc_net {

class EpollServer {
 public:
  // Connection handler interface.
  class EpollConnectionHandler {
   public:
    // Initial context. Parameters can be used for sending packets.
    virtual void set_context(int64 connection_handle,
                             EpollServer* epoll_server) = 0;

    // Upcall packets.
    virtual void handle_buffer(const char* buffer, int byte_count) = 0;

    // Connection handler object can be destroyed after this.
    virtual void finalize() {
      delete this;
    }
  };

  // Connection handler factory interface.
  class EpollConnectionHandlerFactory {
   public:
    virtual EpollConnectionHandler* get() = 0;
  };

  EpollServer(const char* host, const char* port,
              EpollConnectionHandlerFactory* getter, int wait_thread_count);

  ~EpollServer();

  int32 get_actual_port() {
    return actual_port_;
  }

  // Methods that can be called by Connection Handler only.
  void close_connection(int64 connection_handle);
  void send_blocking(int64 connection_handle, const char* buffer,
                     int byte_count);

  // Methods that can be called by lower shim layer.
  void handle_upcall(int64 connection_handle);

 private:
  int64 acceptor_handle_;
  int acceptor_fd_;
  int32 actual_port_;
  EpollConnectionHandlerFactory* getter_;
  cc_shared::scoped_ptr<EpollShim> epoll_shim_;

  cc_shared::scoped_ptr<boost::thread_group> wait_threads_;
  int wait_thread_count_;

  cc_shared::Mutex lock_;
  int64 handle_seed_;
  boost::unordered_map<int64, int> handle_to_fd_lookup_;
  boost::unordered_map<int64, EpollConnectionHandler*> handler_lookup_;
  boost::unordered_map<int64, int> handler_refcount_;

  int64 get_new_connection_handle(int descriptor);

  void wait_worker();

  void do_connection_accept();

  void do_connection_upcall(int64 connection_handle);

  void complete_connection_socket(int64 connection_handle);

  // TODO: Remove map lookup implementation from this class and use the generic
  // implementation in cc_shared::RefcountedLookup.
  void handler_ref(int64 connection_handle);

  void handler_deref(int64 connection_handle);

  void upcall_connection_started(int64 connection_handle);

  void upcall_connection_closed(int64 connection_handle);

  void upcall_handle_buffer(int64 connection_handle, const char* buffer,
                            int byte_count);

  DISALLOW_COPY_AND_ASSIGN(EpollServer);
};


// Getter implementation.
template <typename _ParentType, typename _HandlerType>
class HandlerGetter : public EpollServer::EpollConnectionHandlerFactory {
 public:
  explicit HandlerGetter(_ParentType* parent) : parent_(parent) {
  }

  virtual ~HandlerGetter() {
  }

  virtual EpollServer::EpollConnectionHandler* get() {
    _HandlerType* instance = new(std::nothrow) _HandlerType();
    if (instance) {
      instance->set_parent(parent_);
    }
    return instance;
  }
 private:
  _ParentType* parent_;
  DISALLOW_COPY_AND_ASSIGN(HandlerGetter);
};

}  // cc_net

#endif  // __CC_NET_EPOLL_SERVER__
