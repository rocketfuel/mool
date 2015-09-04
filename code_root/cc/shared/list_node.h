/*Header file for list node module.*/
#ifndef __CC_SHARED_LIST_NODE__
#define __CC_SHARED_LIST_NODE__

#include "cc/shared/common.h"

namespace cc_shared {

// This template based class implements some useful methods to easily implement
// a doubly linked list.

template <typename T>
class ListNode {
 public:
  ListNode() : previous_(this), next_(this) {
  }

  bool is_empty() {
    if (previous_ == this) {
      CHECK_EQ(next_, this);
      return true;
    }
    CHECK_NE(next_, this);
    return false;
  }

  void insert_before(ListNode* other) {
    CHECK(other->is_empty());
    other->previous_ = previous_;
    other->next_ = this;
    previous_->next_ = other;
    previous_ = other;
  }

  void insert_after(ListNode* other) {
    CHECK(other->is_empty());
    other->next_ = next_;
    other->previous_ = this;
    next_->previous_ = other;
    next_ = other;
  }

  ListNode* remove_before() {
    CHECK(!is_empty());
    ListNode* other = previous_;
    previous_ = other->previous_;
    previous_->next_ = this;
    other->previous_ = other->next_ = other;
    return other;
  }

  ListNode* remove_after() {
    CHECK(!is_empty());
    ListNode* other = next_;
    next_ = other->next_;
    next_->previous_ = this;
    other->previous_ = other->next_ = other;
    return other;
  }

  void remove_this() {
    if (is_empty()) {
      return;
    }
    ListNode* previous = previous_;
    ListNode* next = next_;
    previous_ = next_ = this;
    previous->next_ = next;
    next->previous_ = previous;
  }

  T get_item() {
    return item_;
  }

  void set_item(T value) {
    item_ = value;
  }

  ListNode* get_previous() {
    return previous_;
  }

  ListNode* get_next() {
    return next_;
  }

 private:
  ListNode* previous_;
  ListNode* next_;
  T item_;
  DISALLOW_COPY_AND_ASSIGN(ListNode);
};

}  // cc_shared

#endif  // __CC_SHARED_LIST_NODE__
