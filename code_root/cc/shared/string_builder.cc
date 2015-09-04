/*Implementation of string and buffer builder modules.*/
#include "cc/shared/string_builder.h"
#include "cc/shared/scoped_array.h"

#include <vector>

using std::vector;

namespace cc_shared {

namespace {
  static const int kBufferSize = 2015;

}  // namespace

class InnerBufferBuilder {
 public:
  InnerBufferBuilder() : writeable_(true), data_(NULL), buffer_len_(0) {
  }

  ~InnerBufferBuilder() {
    DELETE_POINTER_VECTOR(buffer_);
  }

  void append(const char* read_ptr, int length) {
    CHECK(writeable_) << "Cannot append to locked buffer.";
    CHECK(length >= 0) << "Cannot handle negative length.";
    const char* current = read_ptr;
    int bytes_left = length;
    while (bytes_left > 0) {
      Buffer* last_buffer = get_last_buffer_with_nonzero_capacity();
      int bytes_read = 0;
      last_buffer->load_data(current, &bytes_left, &bytes_read);
      current += bytes_read;
    }
    buffer_len_ += length;
  }

  BufferBuilder::BufferInfo get() {
    commit();
    BufferBuilder::BufferInfo result;
    result.ptr = data_.get();
    result.length = buffer_len_;
    return result;
  }

 private:
  struct Buffer {
    char data[kBufferSize];
    int bytes_used;

    Buffer() : bytes_used(0) {
    }

    int capacity() {
      return kBufferSize - bytes_used;
    }

    void load_data(const char* read_ptr, int* bytes_left, int* bytes_read) {
      (*bytes_read) = 0;
      int bytes_to_copy = std::min(capacity(), (*bytes_left));
      CHECK_LT(0, bytes_to_copy);
      COPY_MEMORY(data + bytes_used, read_ptr, bytes_to_copy);
      bytes_used += bytes_to_copy;
      (*bytes_left) -= bytes_to_copy;
      (*bytes_read) += bytes_to_copy;
    }
  };

  // Keeping a vector of pointers to avoid copying the buffers around. STL can
  // copy the pointers as it pleases.
  vector<Buffer*> buffer_;
  bool writeable_;
  scoped_array<char> data_;
  int buffer_len_;

  Buffer* get_last_buffer_with_nonzero_capacity() {
    bool allocate = ((VSIZE(buffer_) == 0) ||
                     (buffer_[VSIZE(buffer_) - 1]->capacity() == 0));
    if (allocate) {
      buffer_.push_back(new(std::nothrow) Buffer());
    }
    return buffer_[VSIZE(buffer_) - 1];
  }

  void commit() {
    if (!writeable_) {
      // Already committed.
      return;
    }
    CHECK_EQ(NULL, data_.get());
    data_.replace(new(std::nothrow) char [buffer_len_]);
    char* write_ptr = data_.get();
    for (int i = 0; i < VSIZE(buffer_); ++i) {
      const char* read_ptr = buffer_[i]->data;
      COPY_MEMORY(write_ptr, read_ptr, buffer_[i]->bytes_used);
      write_ptr += buffer_[i]->bytes_used;
    }
    DELETE_POINTER_VECTOR(buffer_);
    writeable_ = false;
  }

  DISALLOW_COPY_AND_ASSIGN(InnerBufferBuilder);
};

BufferBuilder::BufferInfo::BufferInfo() : ptr(NULL), length(0) {
}

BufferBuilder::BufferBuilder()
    : inner_(new(std::nothrow) InnerBufferBuilder()){
}

BufferBuilder::~BufferBuilder() {
}

void BufferBuilder::append(const char* read_ptr, int length) {
  inner_->append(read_ptr, length);
}

void BufferBuilder::append_c_str(const char* text) {
  inner_->append(text, strlen(text));
}

void BufferBuilder::append_null_terminator() {
  static const char* kEmpty = "";
  inner_->append(kEmpty, 1);
}

BufferBuilder::BufferInfo BufferBuilder::get() {
  return inner_->get();
}

StringBuilder::StringBuilder() : committed_(false) {
}

StringBuilder::~StringBuilder() {
}

void StringBuilder::append(const char* read_ptr, int length) {
  builder_.append(read_ptr, length);
}

void StringBuilder::append_c_str(const char* text) {
  builder_.append_c_str(text);
}

const char* StringBuilder::c_str() {
  commit();
  return builder_.get().ptr;
}

int StringBuilder::get_str_len() {
  commit();
  return builder_.get().length - 1;
}

void StringBuilder::commit() {
  if (committed_) {
    return;
  }
  builder_.append_null_terminator();
  builder_.get();
  committed_ = true;
}

}  // cc_shared
