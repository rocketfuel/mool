/*Unit tests for mutex module.*/
#include "cc/shared/mutex.h"

#include "gtest/gtest.h"

namespace cc_shared {

TEST(MutexTest, test_simple) {
  Mutex mutex;
  mutex.lock();
  mutex.unlock();
}

TEST(MutexTest, test_reentrant) {
  Mutex mutex;
  mutex.lock();
  mutex.lock();
  mutex.unlock();
  mutex.unlock();
}

TEST(MutexTest, test_safe_acquire) {
  Mutex mutex;
  for (int i = 0; i < 5; ++i) {
    ScopedMutex scoped(&mutex);
  }
}

}  // cc_shared
