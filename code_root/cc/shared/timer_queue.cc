/*Implementation of timer queue module.*/
#include "cc/shared/timer_queue.h"
#include "cc/shared/mutex.h"

#include <map>
#include <vector>

#include <boost/atomic.hpp>
#include <boost/bind.hpp>
#include <boost/thread/thread.hpp>

using std::map;
using std::vector;

namespace cc_shared {

typedef map<int64, vector<TimerCallbackContext> > Maptype;

class InnerTimerQueue {
 public:
  static const int kTimerResponsePeriodMillis;

  InnerTimerQueue(TIMER_CALLBACK callback, int thread_count)
      : callback_(callback), running_(true), stopped_(false) {
    CHECK(thread_count > 0);
    for (int i = 0; i < thread_count; ++i) {
      workers_.create_thread(
          boost::bind(&InnerTimerQueue::worker, this));
    }
  }

  ~InnerTimerQueue() {
    stop();
  }

  void stop() {
    if (stopped_) {
      return;
    }
    running_ = false;
    workers_.join_all();
    stopped_ = true;
  }

  bool add_item(TimerCallbackContext context, int64 epoch_cutoff_millis) {
    cc_shared::ScopedMutex scoped(&lock_);
    if (!running_) {
      return false;
    }
    items_[epoch_cutoff_millis].push_back(context);
    return true;
  }

 private:
  cc_shared::Mutex lock_;
  TIMER_CALLBACK callback_;
  boost::thread_group workers_;
  Maptype items_;
  boost::atomic<bool> running_;
  boost::atomic<bool> stopped_;

  void worker() {
    while (true) {
      bool done = (!running_) && (items_.begin() == items_.end());
      if (done) {
        break;
      }
      vector<TimerCallbackContext> result;
      get_next_batch(&result);
      if (0 != VSIZE(result)) {
        for (int i = 0; i < VSIZE(result); ++i) {
          callback_(result[i]);
        }
      } else {
        usleep(kTimerResponsePeriodMillis * 1000);
      }
    }
  }

  // TODO: Consider fine tuning this further by setting a batch size upper
  // limit. Current implementation pulls out the entire value list for a cutoff
  // key as a batch.
  void get_next_batch(vector<TimerCallbackContext>* result) {
    cc_shared::ScopedMutex scoped(&lock_);
    int64 current_epoch = get_epoch_milliseconds();
    int64 epoch_key = -1;
    for (Maptype::iterator iter = items_.begin(); iter != items_.end();
         ++iter) {
      if (running_ && (iter->first > current_epoch)) {
        // Items are not ready for triggering yet.
        break;
      }
      epoch_key = iter->first;
      for (int i = 0; i < VSIZE(iter->second); ++i) {
        result->push_back(iter->second[i]);
      }
      break;
    }
    if (epoch_key > 0) {
      items_.erase(epoch_key);
    }
  }

  DISALLOW_COPY_AND_ASSIGN(InnerTimerQueue);
};

const int InnerTimerQueue::kTimerResponsePeriodMillis = 5;

TimerQueue::TimerQueue(TIMER_CALLBACK callback, int thread_count)
    : inner_(new(std::nothrow) InnerTimerQueue(callback, thread_count)) {
}

TimerQueue::~TimerQueue() {
}

void TimerQueue::stop() {
  inner_->stop();
}

bool TimerQueue::add_item(TimerCallbackContext context,
                          int64 epoch_cutoff_millis) {
  return inner_->add_item(context, epoch_cutoff_millis);
}

}  // cc_shared
