/* Header file for mutual exclusion.*/
#ifndef __CC_SHARED_MUTEX__
#define __CC_SHARED_MUTEX__

#include "cc/shared/common.h"
#include "cc/shared/scoped_ptr.h"

// Forward declarations.
namespace boost {
class recursive_mutex;
}  // boost

namespace cc_shared {

// Implements a re-entrant mutual exclusion mechanism.
class Mutex {
 public:
  Mutex();

  ~Mutex();

  void lock();

  void unlock();

 private:
  scoped_ptr<boost::recursive_mutex> inner_;

  DISALLOW_COPY_AND_ASSIGN(Mutex);
};

class ScopedMutex {
 public:
  explicit ScopedMutex(Mutex* mutex);
  ~ScopedMutex();

 private:
  DISALLOW_DEFAULT_CONSTRUCTORS(ScopedMutex);
  Mutex* mutex_;
};

}  // cc_shared

#endif  // __CC_SHARED_MUTEX__
