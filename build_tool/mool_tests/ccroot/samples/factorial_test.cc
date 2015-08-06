/*Test file details.*/
#include "ccroot/samples/factorial.h"
#include "gtest/gtest.h"

/* For more complicated tests involving test fixtures, please see
   https://code.google.com/p/googletest/wiki/Primer
*/

namespace ccroot_samples {

TEST(FactorialTest, Negative) {
  EXPECT_EQ(-1, factorial(-5));
}

TEST(FactorialTest, Zero) {
  EXPECT_EQ(1, factorial(0));
}

TEST(FactorialTest, Positive) {
  EXPECT_EQ(1, factorial(1));
  EXPECT_EQ(2, factorial(2));
  EXPECT_EQ(24, factorial(4));
}

TEST(FactorialTest, Large) {
  EXPECT_EQ(3628800, factorial(10));
}

}  // ccroot_samples
