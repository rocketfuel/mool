/*Header file for stream stats module.*/
#ifndef __CC_SHARED_STREAM_STATS__
#define __CC_SHARED_STREAM_STATS__

#include "cc/shared/common.h"
#include "cc/shared/mutex.h"

namespace cc_shared {

class StreamStats {
 public:
  StreamStats();

  ~StreamStats();

  void append(int64 item);

  double get_mean();

 private:
  Mutex lock_;
  int64 count_;
  int64 sum_;
  DISALLOW_COPY_AND_ASSIGN(StreamStats);
};

}  // cc_shared

#endif  // __CC_SHARED_STREAM_STATS__
