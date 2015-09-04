/*Unit test for timer queue module.*/
#include "cc/shared/timer_queue.h"
#include "gtest/gtest.h"

#include <vector>
#include <boost/atomic.hpp>

using std::vector;

namespace cc_shared {

static const int64 kMillisPerHour = 3600000L;
static const int64 kTenMillis = 10000L;

namespace {

class State {
 public:
  State() : count_(0) {
  }

  TimerCallbackContext get_context() {
    TimerCallbackContext context;
    context.value1 = reinterpret_cast<int64>(this);
    return context;
  }

  void increment() {
    ++count_;
  }

  int get_count() {
    return count_;
  }

  static void callback_func(TimerCallbackContext context) {
    State* state = reinterpret_cast<State*>(context.value1);
    state->increment();
  }

 private:
  boost::atomic<int> count_;
  DISALLOW_COPY_AND_ASSIGN(State);
};

}  // namespace

TEST(TimerQueueTest, test_automatic_fire) {
  static const int kIterations = 25;
  State state;
  int64 current_epoch = get_epoch_milliseconds();
  {
    TimerQueue queue(&State::callback_func, 2);
    for (int i = 0; i < kIterations; ++i) {
      bool ok = queue.add_item(state.get_context(),
                               current_epoch + kMillisPerHour + (5 * i));
      EXPECT_TRUE(ok);
    }
  }
  EXPECT_EQ(kIterations, state.get_count());
}

TEST(TimerQueueTest, test_fire) {
  static const int kIterations = 25;
  State state;
  int64 current_epoch = get_epoch_milliseconds();
  TimerQueue queue(&State::callback_func, 2);
  for (int i = 0; i < kIterations; ++i) {
    bool ok = queue.add_item(state.get_context(),
                             current_epoch + 50 + (5 * i));
    EXPECT_TRUE(ok);
  }
  int iters = 0;
  while (true) {
    CHECK_LT(iters, 100) << "Timers did not fire.";
    if (kIterations == state.get_count()) {
      break;
    }
    usleep(kTenMillis);
  }
}

TEST(TimerQueueTest, test_stop) {
  static const int kIterations = 25;
  State state;
  int64 current_epoch = get_epoch_milliseconds();
  TimerQueue queue(&State::callback_func, 2);
  for (int i = 0; i < kIterations; ++i) {
    bool ok = queue.add_item(state.get_context(),
                             current_epoch + kMillisPerHour + (5 * i));
    EXPECT_TRUE(ok);
  }
  queue.stop();
  EXPECT_EQ(kIterations, state.get_count());
  queue.stop();
  EXPECT_EQ(kIterations, state.get_count());
}

}  // cc_shared
