/*Common classes.*/

// Note: Uncomment this line and recompile to enable enhanced logging.
// #define THREAD_LOGGING_ENABLED

#include "cc/shared/common.h"
#include "cc/shared/callback.h"

#include <pthread.h>
#include <time.h>
#include <sys/time.h>
#include <boost/thread/mutex.hpp>
#include <map>

boost::mutex _global_log_lock;

using std::string;

string int_to_text(const char* format_text, int value) {
  static const char kTextSize = 100;
  char text[kTextSize];
  ZERO_MEMORY(text, kTextSize);
  snprintf(text, kTextSize - 5, format_text, value);
  return text;
}

LogMessage::LogMessage(const char* file, int line, bool fatal)
    : fatal_(fatal) {
#ifdef THREAD_LOGGING_ENABLED
  static int64 start_epoch = get_epoch_milliseconds();
  static int last_thread = -1;
  static std::map<void*, int> thread_map;

  int thread_id;
  {
    boost::mutex::scoped_lock lock(_global_log_lock);
    void* thread_self = reinterpret_cast<void*>(pthread_self());
    if (thread_map.find(thread_self) == thread_map.end()) {
      thread_map[thread_self] = ++last_thread;
    }
    thread_id = thread_map[thread_self] + 200;  // The thread id numbers are not
                                                // real thread id's here. We add
                                                // a cosmetic constant to make
                                                // the thread id's appear to
                                                // belong to a group. This helps
                                                // during visual debugging.
  }
  stream() << "tid: " << int_to_text("%3d", thread_id) << " ";
  stream() << "delta_ms: "
           << int_to_text("%4d  ", get_epoch_milliseconds() - start_epoch);
#endif  // THREAD_LOGGING_ENABLED
  stream() << "" << file << ":" << int_to_text("%5d", line) << ": ";
}

LogMessage::~LogMessage() {
  boost::mutex::scoped_lock lock(_global_log_lock);
  const char* delimiter = fatal_ ? "\n\n": "";
  std::clog << delimiter << str_.str() << "\n" << delimiter;
  std::clog.flush();
  if (fatal_) {
    abort();
  }
}

std::ostream& LogMessage::stream() {
  return str_;
}

int64 get_epoch_milliseconds() {
  struct timeval time_val;
  int64 result = 0;
  int status = gettimeofday(&time_val, NULL);
  CHECK_EQ(0, status);
  result += static_cast<int64>(time_val.tv_sec) * 1000L;
  result += static_cast<int64>(time_val.tv_usec) / 1000L;
  return result;
}

timeval millis_to_timeval(int milliseconds) {
  CHECK_LE(0, milliseconds) << "Invalid duration.";
  timeval result;
  result.tv_sec  = milliseconds / 1000;
  result.tv_usec = (milliseconds % 1000) * 1000;
  return result;
}

TraceLogger::TraceLogger(const char* file_name, const char* func_name,
                         int line_no, void* this_ptr)
    : file_name_(file_name), func_name_(func_name), line_no_(line_no),
      this_ptr_(this_ptr) {
  trace_helper("-->> Enter");
}

TraceLogger::~TraceLogger() {
  trace_helper("<<-- Exit ");
}

void TraceLogger::trace_helper(const char* qualifier) {
  LogMessage logger(file_name_, line_no_, false);
  logger.stream() << qualifier;
  if (this_ptr_) {
    logger.stream() << "(" << this_ptr_ << ") ";
  } else {
    logger.stream() << " ";
  }
  logger.stream() << func_name_;
}

string percentage_text(int64 numerator, int64 denominator) {
  double ratio = (1 + numerator) * 1.0 / (1 + denominator);
  ratio *= 100.0;
  char result[100];
  sprintf(result, "%6.2f%%", ratio);
  return result;
}

// ===================================================================
// emulates google3/base/callback.cc
// copied from google protobuf code.

namespace cc_shared {

Closure::~Closure() {}

namespace internal { FunctionClosure0::~FunctionClosure0() {} }

void do_nothing() {}

}  // namespace cc_shared
