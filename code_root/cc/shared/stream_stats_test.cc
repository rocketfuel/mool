/*Unit test for stream stats module.*/
#include "cc/shared/stream_stats.h"
#include "gtest/gtest.h"

namespace cc_shared {

TEST(StreamStatsTest, test_simple) {
  StreamStats stream_stats;
  stream_stats.append(1.0);
  stream_stats.append(3.0);
  ASSERT_NEAR(2.0, stream_stats.get_mean(), 0.1);
}

}  // cc_shared
