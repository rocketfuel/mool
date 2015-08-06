/*Test file details.*/
#include "ccroot/samples/use_interface.h"

#include "gmock/gmock.h"
#include "gtest/gtest.h"

namespace ccroot_samples {

class MockInterface : public UseInterface {
 public:
  MOCK_METHOD0(use, void());
};

TEST(UseInterfaceTest, MockTest) {
  MockInterface mock_object;
  EXPECT_CALL(mock_object, use());
  use_interface(&mock_object);
}

}  // ccroot_samples
