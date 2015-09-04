/*Header file for refcounted lookup module.*/
#ifndef __CC_SHARED_REFCOUNTED_LOOKUP__
#define __CC_SHARED_REFCOUNTED_LOOKUP__

#include "cc/shared/callback.h"
#include "cc/shared/common.h"
#include "cc/shared/scoped_ptr.h"

namespace cc_shared {

// Forward declaration.
class InnerLookup;

class RefcountedLookup {
 public:
  RefcountedLookup();

  ~RefcountedLookup();

  // Creates and returns a new reference id for the specified context and
  // finalizer. Initial reference count of the object is 1. The context
  // parameter must be non-NULL.
  int64 get_new_id(void* context, Closure* finalizer);

  // Increment reference count and get the context back. If id is not a valid
  // reference, return value is NULL.
  void* addref_and_get(int64 id);

  // Decrement reference count. If count gets to zero finalizer is called in the
  // same thread. Id must be a valid reference. It is possible to club multiple
  // dereference calls into one.
  void deref(int64 id, int deref_count);

  // Typically called before destruction. Resets all ref counts to zeros, cleans
  // all internal contexts and calls all finalizers. Should be called only after
  // processing threads have stopped.
  void clean_all_contexts();

 private:
  cc_shared::scoped_ptr<InnerLookup> inner_;
  DISALLOW_COPY_AND_ASSIGN(RefcountedLookup);
};


}  // cc_shared

#endif  // __CC_SHARED_REFCOUNTED_LOOKUP__
