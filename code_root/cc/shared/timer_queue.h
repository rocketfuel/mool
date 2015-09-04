/*Header file for timer queue module.*/
#ifndef __CC_SHARED_TIMER_QUEUE__
#define __CC_SHARED_TIMER_QUEUE__

#include "cc/shared/common.h"
#include "cc/shared/scoped_ptr.h"

namespace cc_shared {

// Forward declaration.
class InnerTimerQueue;

struct TimerCallbackContext {
  int64 value1;
  int64 value2;
};

typedef void (*TIMER_CALLBACK)(TimerCallbackContext context);

class TimerQueue {
 public:
  TimerQueue(TIMER_CALLBACK callback, int thread_count);

  ~TimerQueue();

  // Stop accepting new requests and wait for threads to finish all the added
  // tasks. This is an idempotent method. I.e. it is safe to stop a stopped
  // timer queue.
  void stop();

  // Call the provided callback (in the constructor) with the provided context
  // (parameter to this method) anytime after epoch_cutoff_millis. All saved
  // requests are fired immediately if object is destroyed.
  // Callback threads check for fired events every 5 milliseconds.
  // Return value is true if addition succeeded. It can be false if object has
  // started de-initialization.
  bool add_item(TimerCallbackContext context, int64 epoch_cutoff_millis);

 private:
  cc_shared::scoped_ptr<InnerTimerQueue> inner_;
  DISALLOW_COPY_AND_ASSIGN(TimerQueue);
};

}  // cc_shared

#endif  // __CC_SHARED_TIMER_QUEUE__
