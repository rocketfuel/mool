// Sample C++ binary using the factorial library.
#include "ccroot/samples/factorial.h"

#include "ccroot/common/echo_utils.h"
#include "ccroot/common/some_lib.h"
#include "ccroot/common/global_macros.h"

#include <stdio.h>
#include <string.h>

#include <boost/regex.hpp>

using std::string;

int main(int argc, char* argv[]) {
  CHECK(true);
  ccroot_common::echo("\nHello, world.\n");
  CHECK(-1 == ccroot_common::get_special_number());
  ccroot_samples::print_math_number();
  static const int kValue = 9;
  printf("Factorial(%d) = %d\n", kValue,
         ccroot_samples::factorial(kValue));

  static const boost::regex r("a.*");
  CHECK(boost::regex_match("a jolly good fellow", r));
  CHECK(!boost::regex_match("is a very good person", r));
}
