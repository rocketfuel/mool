/*Unit test for assigned pool module.*/
#include "cc/net/assigned_pool.h"
#include "gtest/gtest.h"
#include <time.h>
#include <stack>

using std::stack;

namespace cc_net {

TEST(AssignedPoolTest, test_simple) {
  int64 value = -1;
  AssignedPool pool;
  ASSERT_FALSE(pool.get_candidate(NULL));

  pool.insert(2L);
  ASSERT_TRUE(pool.get_candidate(&value));
  ASSERT_EQ(2L, value);

  ASSERT_FALSE(pool.get_candidate(NULL));

  pool.erase(3L);
  ASSERT_FALSE(pool.get_candidate(NULL));

  pool.insert(3L);
  ASSERT_TRUE(pool.get_candidate(&value));
  ASSERT_EQ(3L, value);

  ASSERT_FALSE(pool.get_candidate(NULL));
}

TEST(AssignedPoolTest, test_batch) {
  static const int64 kIterations = 1000;
  int64 value = -1;
  AssignedPool pool;

  for (int64 i = 0; i < kIterations; ++i) {
    pool.insert(i);
  }

  for (int64 i = 0; i < kIterations; ++i) {
    int64 expected_value = kIterations - 1 - i;
    if (0 == (i % 2)) {
      ASSERT_TRUE(pool.get_candidate(&value));
      ASSERT_EQ(expected_value, value);
    } else {
      pool.erase(expected_value);
    }
  }

  ASSERT_FALSE(pool.get_candidate(NULL));
}

TEST(AssignedPoolTest, test_mixed) {
  static const int64 kIterations = 1L << 15;
  int64 value = -1;
  AssignedPool pool;
  stack<int64> control;
  srand (time(NULL));

  ASSERT_FALSE(pool.get_candidate(NULL));
  for (int64 i = 0; i < kIterations; ++i) {
    int operation = rand() % 3;
    if (0 == operation) {
      // Insertion tests.
      int64 item = rand();
      pool.insert(item);
      control.push(item);
    } else if (1 == operation) {
      // Checkout tests.
      bool found = pool.get_candidate(&value);
      if (found) {
        EXPECT_LT(0, control.size());
        EXPECT_EQ(control.top(), value);
        control.pop();
      } else {
        EXPECT_EQ(0, control.size());
      }
    } else {
      // Erase tests.
      if (control.size() > 0) {
        value = control.top();
        control.pop();
        pool.erase(value);
      }
    }
  }
  for (int i = 0; i < static_cast<int32>(control.size()); ++i) {
    EXPECT_TRUE(pool.get_candidate(&value));
  }
  ASSERT_FALSE(pool.get_candidate(NULL));
}

}  // cc_net
