/*Test file details.*/
#include "ccroot/common/some_lib.h"
#include "gtest/gtest.h"
#include <math.h>

namespace ccroot_common {

TEST(SomeLibTest, math_number_test) {
  EXPECT_GT(0.0001, fabs(get_math_number() - 1.41421356));
}

TEST(SomeLibTest, special_number_test) {
  EXPECT_EQ(-1, get_special_number());
}

}  // ccroot_common
