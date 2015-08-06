/*Test file details.*/
#include "gtest/gtest.h"

namespace ccroot_failures {

TEST(FailuresTest, mem_leak_test) {
  // Intentional memory leak that valgrind should catch.
  int* p = new int;
}

}  // ccroot_failures
