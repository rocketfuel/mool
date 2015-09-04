/*Unit tests for socket utils.*/
#include "cc/net/socket_utils.h"
#include "gtest/gtest.h"

using std::string;

namespace cc_net {

TEST(SocketUtilsTest, test_get_ipv4_name) {
  static const int32 kLocalHost = 0x7F000001;
  static const char* kExpected = "127.0.0.1";
  string actual;
  int result = SocketUtils::get_ip_v4_name(kLocalHost, &actual);
  EXPECT_EQ(0, result);
  EXPECT_STREQ(kExpected, actual.c_str());
}

TEST(SocketUtilsTest, test_get_address_port_text) {
  static const int32 kLocalHost = 0x7F000001;
  static const int32 kPort = 1234;
  static const char* kExpected = "127.0.0.1:1234";
  string actual;
  int result = SocketUtils::get_address_port_text(kLocalHost, kPort, &actual);
  EXPECT_EQ(0, result);
  EXPECT_STREQ(kExpected, actual.c_str());
}

}  // namespace cc_net
