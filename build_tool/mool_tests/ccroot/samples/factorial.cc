/*Code file details.*/
#include "ccroot/samples/factorial.h"
#include "ccroot/common/some_lib.h"
#include <stdio.h>

namespace ccroot_samples {

void print_math_number() {
  printf("%.5f\n", ccroot_common::get_math_number());
}

int factorial(int n) {
  if (n < 0) {
    return ccroot_common::get_special_number();
  }
  int product = 1;
  for (;n > 0; --n) {
    product *= n;
  }
  return product;
}

}  // ccroot_samples
