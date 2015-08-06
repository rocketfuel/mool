/*Header file details.*/
#ifndef __CCROOT_COMMON_ECHO_UTILS__
#define __CCROOT_COMMON_ECHO_UTILS__

#include <string>

namespace ccroot_common {

using std::string;

// This header file shows a sample library for demonstrating cross directory
// dependencies.
void echo(const string& text);

}  // ccroot_common

#endif  // __CCROOT_COMMON_ECHO_UTILS__
