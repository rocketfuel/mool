/*Implementation of mutex module.*/
#include "cc/shared/mutex.h"

#include "cc/shared/common.h"
#include <boost/thread/recursive_mutex.hpp>

namespace cc_shared {

Mutex::Mutex()
    : inner_(new(std::nothrow) boost::recursive_mutex) {
}

Mutex::~Mutex() {
}

void Mutex::lock() {
  inner_->lock();
}

void Mutex::unlock() {
  inner_->unlock();
}

ScopedMutex::ScopedMutex(Mutex* mutex) : mutex_(mutex) {
  mutex_->lock();
}

ScopedMutex::~ScopedMutex() {
  mutex_->unlock();
  // Note: Here is an alternative implementation of this.
  // boost::recursive_mutex x;
  // boost::recursive_mutex::scoped_lock lock(x);
}

}  // cc_shared
