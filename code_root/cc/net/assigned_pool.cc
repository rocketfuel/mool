/*Implementation of assigned pool module.*/
// Enable for miscellaneous logging.
// #define CC_TRACE_ENABLED
#include "cc/net/assigned_pool.h"
#include "cc/shared/list_node.h"
#include "cc/shared/mutex.h"

#include <boost/unordered_map.hpp>

using cc_shared::ListNode;

namespace cc_net {

class InnerAssignedPool {
 public:
  InnerAssignedPool() {
  }

  ~InnerAssignedPool() {
    while (!(list_head_.is_empty())) {
      erase_util(list_head_.remove_after());
    }
    CHECK(list_head_.is_empty());
    CHECK(lookup_.begin() == lookup_.end());
  }

  void insert(int64 item) {
    cc_shared::ScopedMutex scoped(&lock_);
    CHECK(lookup_.end() == lookup_.find(item));
    NodeType* node = new(std::nothrow) NodeType();
    node->set_item(item);
    lookup_[item] = node;
    list_head_.insert_after(node);
  }

  void erase(int64 item) {
    cc_shared::ScopedMutex scoped(&lock_);
    MapType::iterator finder = lookup_.find(item);
    if (lookup_.end() == finder) {
      return;
    }
    NodeType* node = finder->second;
    CHECK_EQ(item, finder->first);
    CHECK_EQ(item, node->get_item());
    erase_util(node);
  }

  bool get_candidate(int64* value) {
    cc_shared::ScopedMutex scoped(&lock_);
    if (list_head_.is_empty()) {
      return false;
    }
    NodeType* node = list_head_.get_next();
    (*value) = node->get_item();
    erase_util(node);
    return true;
  }

 private:
  cc_shared::Mutex lock_;
  typedef ListNode<int64> NodeType;
  typedef boost::unordered_map<int64, NodeType*> MapType;
  MapType lookup_;
  NodeType list_head_;

  void erase_util(NodeType* node) {
    node->remove_this();
    lookup_.erase(node->get_item());
    delete node;
  }

  DISALLOW_COPY_AND_ASSIGN(InnerAssignedPool);
};

AssignedPool::AssignedPool() : inner_(new(std::nothrow) InnerAssignedPool()) {
}

AssignedPool::~AssignedPool() {
}

void AssignedPool::insert(int64 item) {
  TRACE_FILE_EVENT(__FUNCTION__ << " " << item);
  inner_->insert(item);
}

void AssignedPool::erase(int64 item) {
  TRACE_FILE_EVENT(__FUNCTION__ << " " << item);
  inner_->erase(item);
}

bool AssignedPool::get_candidate(int64* value) {
  bool result = inner_->get_candidate(value);
  TRACE_FILE_EVENT(__FUNCTION__ << " returned " << result << " value = "
                   << (result ? (*value) : -1));
  return result;
}

}  // cc_net
