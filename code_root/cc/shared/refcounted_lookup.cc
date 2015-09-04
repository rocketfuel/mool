/*Implementation of refcounted lookup module.*/
// Enable for API events (in both directions).
// #define TRACE_API_EVENTS
#include "cc/shared/refcounted_lookup.h"
#include "cc/shared/mutex.h"

#include <boost/unordered_map.hpp>

using boost::unordered_map;

namespace cc_shared {

class InnerLookup {
 public:
  InnerLookup() : seed_(-1) {
  }

  ~InnerLookup() {
    CHECK_EQ(0, static_cast<int32>(lookup_.size()));
  }

  int64 get_new_id(void* context, Closure* finalizer) {
    CHECK_NE(NULL, context) << "NULL is not a valid context.";
    ScopedMutex scoped(&lock_);
    int64 id = ++seed_;
    CHECK(lookup_.end() == lookup_.find(id));
    Context* old_context = lookup_[id].replace(new(std::nothrow) Context());
    CHECK_EQ(NULL, old_context);
    Context* new_context = lookup_[id].get();
    new_context->ref_count = 1;
    new_context->outer_context = context;
    new_context->finalizer = finalizer;
    TRACE_API_EVENT("get_new_id " << context << " " << id);
    return id;
  }

  void* addref_and_get(int64 id) {
    TRACE_API_EVENT("addref id:" << id << " +" << 1);
    ScopedMutex scoped(&lock_);
    LookupType::iterator iter = lookup_.find(id);
    if (iter == lookup_.end()) {
      return NULL;
    }
    Context* context = iter->second.get();
    context->ref_count += 1;
    return context->outer_context;
  }

  void deref(int64 id, int deref_count) {
    TRACE_API_EVENT("deref id:" << id << " -" << deref_count);
    CHECK_LE(1, deref_count);
    Closure* finalizer = NULL;
    {
      ScopedMutex scoped(&lock_);
      Context* context = lookup_[id].get();
      context->ref_count -= deref_count;
      if (0 == context->ref_count) {
        finalizer = context->finalizer;
        lookup_[id].reset();
        lookup_.erase(id);
      }
    }
    if (finalizer) {
      finalizer->Run();
    }
  }

  void clean_all_contexts() {
    TRACE_API_EVENT("clean_all_contexts");
    ScopedMutex scoped(&lock_);
    for (LookupType::iterator iter = lookup_.begin(); iter != lookup_.end();
         ++iter) {
      iter->second->finalizer->Run();
    }
    lookup_.clear();
  }

 private:
  struct Context {
    int ref_count;
    void* outer_context;
    Closure* finalizer;
  };
  Mutex lock_;
  typedef unordered_map<int64, scoped_ptr<Context> > LookupType;
  LookupType lookup_;
  int64 seed_;
  DISALLOW_COPY_AND_ASSIGN(InnerLookup);
};

RefcountedLookup::RefcountedLookup()
    : inner_(new(std::nothrow) InnerLookup()) {
}

RefcountedLookup::~RefcountedLookup() {
}

int64 RefcountedLookup::get_new_id(void* context, Closure* finalizer) {
  return inner_->get_new_id(context, finalizer);
}

void* RefcountedLookup::addref_and_get(int64 id) {
  return inner_->addref_and_get(id);
}

void RefcountedLookup::deref(int64 id, int deref_count) {
  inner_->deref(id, deref_count);
}

void RefcountedLookup::clean_all_contexts() {
  inner_->clean_all_contexts();
}

}  // cc_shared
