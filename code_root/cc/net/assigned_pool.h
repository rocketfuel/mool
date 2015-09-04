/*Header file for assigned pool module.*/
#ifndef __CC_NET_ASSIGNED_POOL__
#define __CC_NET_ASSIGNED_POOL__

#include "cc/shared/common.h"
#include "cc/shared/scoped_ptr.h"

namespace cc_net {

// Forward declaration.
class InnerAssignedPool;

// This class essentially implements a linked hash set to provide O(1)
// insertion, removal and iteration (over insertion order). The current
// implementation assumes an int64 record type. That can be easily changed to
// use a templated type, if needed.

// AssignedPool is thread safe.

class AssignedPool {
 public:
  AssignedPool();

  ~AssignedPool();

  void insert(int64 item);

  void erase(int64 item);

  // Preferably a more recently added one. Return true if value found, false
  // otherwise.
  bool get_candidate(int64* value);

 private:
  cc_shared::scoped_ptr<InnerAssignedPool> inner_;
  DISALLOW_COPY_AND_ASSIGN(AssignedPool);
};

}  // cc_net

#endif  // __CC_NET_ASSIGNED_POOL__
