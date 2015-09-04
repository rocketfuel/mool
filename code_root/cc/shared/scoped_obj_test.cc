/*Unit tests for scoped_ptr and scoped_array modules.*/
#include "cc/shared/scoped_ptr.h"
#include "cc/shared/scoped_array.h"

#include "gtest/gtest.h"

namespace cc_shared {

namespace {

class Counter {
 public:
  Counter() : accumulator_(NULL) {
  }

  explicit Counter(int* accumulator) : accumulator_(accumulator) {
  }

  ~Counter() {
    ++(*accumulator_);
  }

  void set_accumulator(int* accumulator) {
    accumulator_ = accumulator;
  }

  int* get_accumulator() {
    return accumulator_;
  }

 private:
  int* accumulator_;
};

}  // namespace


TEST(ScopedObjTest, test_scoped_ptr) {
  // Test scope and ptr dereference.
  int accumulator = 0;
  {
    scoped_ptr<Counter> counter(new(std::nothrow) Counter(&accumulator));
    EXPECT_EQ(&accumulator, counter->get_accumulator());
  }
  EXPECT_EQ(1, accumulator);

  // Test '*', get, reset, replace and release.
  {
    scoped_ptr<int> value(new(std::nothrow) int(0));
    EXPECT_EQ(0, *value);
    (*value) += 23;
    EXPECT_EQ(23, *value);

    {
      int* ptr = value.get();
      EXPECT_EQ(23, *ptr);
    }

    value.reset();
    EXPECT_EQ(NULL, value.get());

    int* old_value = value.replace(new(std::nothrow) int(34));
    EXPECT_EQ(34, *value);
    EXPECT_EQ(NULL, old_value);

    int* temp_value = value.replace(new(std::nothrow) int(23));
    EXPECT_EQ(23, *value);
    EXPECT_EQ(34, *temp_value);
    delete temp_value;

    temp_value = value.release();
    EXPECT_EQ(NULL, value.get());
    EXPECT_EQ(23, *temp_value);
    delete temp_value;
  }
}

TEST(ScopedObjTest, test_scoped_array) {
  const static int kCounters = 3;
  int accumulator = 0;
  {
    scoped_array<Counter> counter(new(std::nothrow) Counter [kCounters]);
    for (int i = 0; i < kCounters; ++i) {
      counter[i].set_accumulator(&accumulator);
    }
  }
  EXPECT_EQ(kCounters, accumulator);

  // Test [], replace and reset.
  {
    scoped_array<int> value(new(std::nothrow) int [kCounters]);
    for (int i = 0; i < kCounters; ++i) {
      value[i] = i;
    }

    {
      int* ptr = value.get();
      for (int i = 0; i < kCounters; ++i) {
        EXPECT_EQ(i, ptr[i]);
      }
    }

    value.reset();
    EXPECT_EQ(NULL, value.get());

    int* old_value = value.replace(new(std::nothrow) int [kCounters]);
    EXPECT_EQ(NULL, old_value);
    EXPECT_TRUE(NULL != value.get());
  }
}

}  // cc_shared
