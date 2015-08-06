/*Code file details.*/
#include "ccroot/common/echo_utils.h"

#include <stdio.h>

namespace ccroot_common {

void echo(const string& text) {
  printf("%s\n", text.c_str());
}

}  // ccroot_common
