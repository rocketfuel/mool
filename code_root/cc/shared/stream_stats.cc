/*Implementation of stream stats module.*/
#include "cc/shared/stream_stats.h"

namespace cc_shared {

StreamStats::StreamStats() : count_(0), sum_(0) {
}

StreamStats::~StreamStats() {
}

void StreamStats::append(int64 item) {
  ScopedMutex scoped(&lock_);
  ++count_;
  sum_ += item;
}

double StreamStats::get_mean() {
  ScopedMutex scoped(&lock_);
  CHECK_NE(0, count_);
  return 1.0 * sum_ / count_;
}

}  // cc_shared
