/*
Copyright 2008, Google Inc.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

    * Redistributions of source code must retain the above copyright
notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above
copyright notice, this list of conditions and the following disclaimer
in the documentation and/or other materials provided with the
distribution.
    * Neither the name of Google Inc. nor the names of its
contributors may be used to endorse or promote products derived from
this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

Header and implementation of scoped array.
Adapted from scoped_ptr class in google mock.
*/
#ifndef __CC_SHARED_SCOPED_ARRAY__
#define __CC_SHARED_SCOPED_ARRAY__

#include "cc/shared/common.h"

namespace cc_shared {

template <typename T>
class scoped_array {
 public:
  explicit scoped_array(T* data) : data_(data) {
  }

  ~scoped_array() {
    reset();
  }

  T* get() const {
    return data_;
  }

  T& operator[](int index) const {
    return data_[index];
  }

  // Force the scoped array to release the pointer. It becomes caller's
  // responsibility to return the memory to operating system.
  T* release() {
    return replace(NULL);
  }

  // Force the scoped array to replace the pointer. It becomes caller's
  // responsibility to return the memory to operating system.
  T* replace(T* data) {
    T* result = data_;
    data_ = data;
    return result;
  }

  void reset() {
    delete [] data_;
    data_ = NULL;
  }

 private:
  T* data_;
  DISALLOW_COPY_AND_ASSIGN(scoped_array);
};

}  // cc_shared

#endif  // __CC_SHARED_SCOPED_ARRAY__
