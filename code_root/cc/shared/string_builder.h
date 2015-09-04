/* Header file for string builder.*/
#ifndef __CC_SHARED_STRING_BUILDER__
#define __CC_SHARED_STRING_BUILDER__

#include "cc/shared/common.h"
#include "cc/shared/scoped_ptr.h"

namespace cc_shared {

// Forward declaration.
class InnerBufferBuilder;

class BufferBuilder {
 public:
  struct BufferInfo {
    BufferInfo();
    char* ptr;
    int length;
  };

  BufferBuilder();

  ~BufferBuilder();

  void append(const char* read_ptr, int length);

  // Appends characters from a NULL-terminated string. Does not append the NULL
  // terminator.
  void append_c_str(const char* text);

  // Appends a single NULL terminator byte.
  void append_null_terminator();

  BufferInfo get();

 private:
  scoped_ptr<InnerBufferBuilder> inner_;
  DISALLOW_COPY_AND_ASSIGN(BufferBuilder);
};

class StringBuilder {
 public:
  StringBuilder();

  ~StringBuilder();

  void append(const char* read_ptr, int length);

  void append_c_str(const char* text);

  const char* c_str();

  int get_str_len();

 private:
  BufferBuilder builder_;
  bool committed_;

  void commit();
  DISALLOW_COPY_AND_ASSIGN(StringBuilder);
};

}  // cc_shared

#endif  // __CC_SHARED_STRING_BUILDER__
