/*Unit test for refcounted lookup module.*/
#include "cc/shared/refcounted_lookup.h"
#include "gtest/gtest.h"

#include <vector>
#include <boost/atomic.hpp>

using std::vector;

namespace cc_shared {

namespace {

struct State {
  State() : count(0) {
  }

  // We don't need an atomic integer since current thread is single threaded,
  // however there is no harm in using it to demonstrate how to do things
  // correctly in a multi-threaded scenario.
  boost::atomic<int> count;

  void increment() {
    ++count;
  }
};

}  // namespace

TEST(RefcountedLookupTest, test_with_new_and_deref) {
  static const int kIterations = 17;
  State state;
  int dummy_context = 0;
  RefcountedLookup lookup;
  vector<int64> id_collection;

  CHECK_EQ(0, state.count);
  for (int i = 0; i < kIterations; ++i) {
    int64 id = lookup.get_new_id(
        &dummy_context, NewCallback(&state, &State::increment));
    id_collection.push_back(id);
  }
  CHECK_EQ(0, state.count);
  for (int i = 0; i < VSIZE(id_collection); ++i) {
    lookup.deref(id_collection[i], 1);
  }
  CHECK_EQ(kIterations, state.count);
}

TEST(RefcountedLookupTest, test_with_ref_use_and_deref) {
  static const int kIterations = 17;
  State state;
  int dummy_context = 0;
  RefcountedLookup lookup;
  vector<int64> id_collection;

  CHECK_EQ(0, state.count);
  for (int i = 0; i < kIterations; ++i) {
    int64 id = lookup.get_new_id(
        &dummy_context, NewCallback(&state, &State::increment));
    id_collection.push_back(id);
  }
  CHECK_EQ(0, state.count);
  for (int i = 0; i < VSIZE(id_collection); ++i) {
    void* context = lookup.addref_and_get(id_collection[i]);
    CHECK_EQ(reinterpret_cast<void*>(&dummy_context), context);
  }
  CHECK_EQ(0, state.count);
  for (int i = 0; i < VSIZE(id_collection); ++i) {
    lookup.deref(id_collection[i], 2);
  }
  CHECK_EQ(kIterations, state.count);
  for (int i = 0; i < VSIZE(id_collection); ++i) {
    void* context = lookup.addref_and_get(id_collection[i]);
    CHECK_EQ(NULL, context);
  }
  CHECK_EQ(kIterations, state.count);
}

TEST(RefcountedLookupTest, test_with_ref_and_clean) {
  static const int kIterations = 17;
  State state;
  int dummy_context = 0;
  scoped_ptr<RefcountedLookup> lookup(new(std::nothrow) RefcountedLookup);
  vector<int64> id_collection;

  CHECK_EQ(0, state.count);
  for (int i = 0; i < kIterations; ++i) {
    int64 id = lookup->get_new_id(
        &dummy_context, NewCallback(&state, &State::increment));
    id_collection.push_back(id);
  }
  CHECK_EQ(0, state.count);
  for (int i = 0; i < VSIZE(id_collection); ++i) {
    void* context = lookup->addref_and_get(id_collection[i]);
    CHECK_EQ(reinterpret_cast<void*>(&dummy_context), context);
  }
  CHECK_EQ(0, state.count);
  lookup->clean_all_contexts();
  lookup.reset();
  CHECK_EQ(kIterations, state.count);
}

}  // cc_shared
