/*Code file details.*/
#include "ccroot/common/some_lib.h"
#include <math.h>

namespace ccroot_common {

double get_math_number() {
  return sqrt(2.0);
}

int get_special_number() {
  static const int kSpecialNumber = -1;
  return kSpecialNumber;
}

}  // ccroot_common
