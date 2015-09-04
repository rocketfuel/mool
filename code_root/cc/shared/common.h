/*Common macros.*/
#ifndef __CC_SHARED_COMMON__
#define __CC_SHARED_COMMON__

#include <stdlib.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

// For nothrow.
#include <new>
#include <iostream>
#include <sstream>

// Compile time assert.
#define CT_ASSERT(_x) \
  extern int _dummy_array_for_compile_time_assert[(_x) ? 1 : -1];

// Standard integer type definitions.
typedef int64_t int64;
typedef int32_t int32;
typedef uint64_t uint64;
typedef uint32_t uint32;

// Codebase can safely assume the following everywhere.
CT_ASSERT(8 == sizeof(long));
CT_ASSERT(8 == sizeof(int64));
CT_ASSERT(8 == sizeof(uint64));
CT_ASSERT(4 == sizeof(int));
CT_ASSERT(4 == sizeof(int32));
CT_ASSERT(4 == sizeof(uint32));
CT_ASSERT(1 == sizeof(char));

// A macro to disallow the copy constructor and operator= functions
// This should be used in the private: declarations for a class.
#define DISALLOW_COPY_AND_ASSIGN(TypeName) \
  TypeName(const TypeName&);               \
  void operator=(const TypeName&)          \

#define DISALLOW_DEFAULT_CONSTRUCTORS(TypeName) \
  TypeName(); \
  DISALLOW_COPY_AND_ASSIGN(TypeName); \

// Simplified version of Google's logging copied from re2/.../logging.h.
class LogMessage {
 public:
  LogMessage(const char* file, int line, bool fatal);
  ~LogMessage();
  std::ostream& stream();

 private:
  DISALLOW_DEFAULT_CONSTRUCTORS(LogMessage);
  bool fatal_;
  std::ostringstream str_;
};

#define LOG_INFO  LogMessage(__FILE__, __LINE__, false)
#define LOG_FATAL LogMessage(__FILE__, __LINE__, true)
#define LOG(severity) LOG_ ## severity.stream()

// Run time assert.
#define CHECK(_x) if (_x) { } else LOG(FATAL) \
    << "Runtime assert failed: '" << #_x << "' "


#define CHECK_EQ(_expected, _actual) CHECK((_expected) == (_actual))
#define CHECK_GT(_first, _second) CHECK((_first) > (_second))
#define CHECK_LT(_first, _second) CHECK((_first) < (_second))
#define CHECK_GE(_first, _second) CHECK((_first) >= (_second))
#define CHECK_LE(_first, _second) CHECK((_first) <= (_second))
#define CHECK_NE(_unexpected, _actual) CHECK((_unexpected) != (_actual))

#define ZERO_MEMORY(_ptr, _size) memset((_ptr), 0, (_size));
#define COPY_MEMORY(_dst, _src, _size) memcpy((_dst), (_src), (_size));

#define ARRAY_SIZE(_x) static_cast<int>(sizeof((_x)) / sizeof((_x)[0]))
#define ZERO_ARRAY(_x) ZERO_MEMORY((_x), sizeof(_x));

// Vectors have a size that return size_t. For all practical purposes, this
// value can be cast to a signed integer. Codebase can safely assume that
// this is always the case.
#define VSIZE(_v) static_cast<int>((_v).size())

// Delete vector of pointers.
#define DELETE_POINTER_VECTOR(_x) { \
  for (int i = 0; i < VSIZE(_x); ++i) { \
    delete (_x)[i]; \
    (_x)[i] = NULL; \
  } \
  (_x).clear(); \
}

// Get current epoch.
int64 get_epoch_milliseconds();

// Milliseconds to struct timeval.
timeval millis_to_timeval(int milliseconds);

// Percentage utility.
std::string percentage_text(int64 numerator, int64 denominator);

class TraceLogger {
 public:
  TraceLogger(const char* file_name, const char* func_name, int line_no,
              void* this_ptr);
  ~TraceLogger();

 private:
  const char* file_name_;
  const char* func_name_;
  int32 line_no_;
  void* this_ptr_;
  void trace_helper(const char* qualifier);
  DISALLOW_COPY_AND_ASSIGN(TraceLogger);
};

#ifdef CC_TRACE_ENABLED
#define _TRACE_METHOD TraceLogger __trace_method ## __LINE__ ( \
    __FILE__, __FUNCTION__, __LINE__, this);
#define _TRACE_FUNC TraceLogger  __trace_func ## __LINE__ ( \
    __FILE__, __FUNCTION__, __LINE__, NULL);
#define TRACE_FILE_EVENT(_x) LOG(INFO) << _x;
#else
#define _TRACE_METHOD
#define _TRACE_FUNC
#define TRACE_FILE_EVENT(_x)
#endif   // CC_TRACE_ENABLED


#ifdef TRACE_API_EVENTS
#define TRACE_API_EVENT(_x) LOG(INFO) << _x;
#else
#define TRACE_API_EVENT(_x)
#endif  // TRACE_FILE_EVENTS

#endif  // __CC_SHARED_COMMON__
