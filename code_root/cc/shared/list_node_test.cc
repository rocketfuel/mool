/*Unit test for list node module.*/
#include "cc/shared/list_node.h"
#include "gtest/gtest.h"

using std::string;

namespace cc_shared {

typedef ListNode<int32> TestNode;

namespace {

string to_text(int32 value) {
  char text[100];
  sprintf(text, "%d", value);
  return text;
}

string to_string_forward(TestNode* node) {
  string result = "";
  bool first = true;
  for (TestNode* curr = node->get_next(); curr != node;
       curr = curr->get_next()) {
    result += first ? "": " ";
    result += to_text(curr->get_item());
    first = false;
  }
  return result;
}

string to_string_reverse(TestNode* node) {
  string result = "";
  bool first = true;
  for (TestNode* curr = node->get_previous(); curr != node;
       curr = curr->get_previous()) {
    result += first ? "": " ";
    result += to_text(curr->get_item());
    first = false;
  }
  return result;
}

void validate(const char* expected_forward_text,
              const char* expected_reverse_text,
              TestNode* test_node) {
  string forward = to_string_forward(test_node);
  string reverse = to_string_reverse(test_node);
  CHECK_EQ(0, strcmp(expected_forward_text, forward.c_str()));
  CHECK_EQ(0, strcmp(expected_reverse_text, reverse.c_str()));
}

}  // namespace

TEST(ListNodeTest, test_empty) {
  TestNode node;
  validate("", "", &node);
  ASSERT_TRUE(node.is_empty());
}

TEST(ListNodeTest, test_simple) {
  static const int kCount = 10;
  TestNode node;
  TestNode nodes[kCount];
  for (int i = 0; i < kCount; ++i) {
    nodes[i].set_item(i);
  }
  for (int i = 0; i < kCount; ++i) {
    node.insert_before(nodes + i);
  }
  ASSERT_FALSE(node.is_empty());
  validate("0 1 2 3 4 5 6 7 8 9", "9 8 7 6 5 4 3 2 1 0", &node);

  TestNode* removed = node.remove_before();
  ASSERT_EQ(nodes + kCount - 1, removed);
  removed = node.remove_after();
  ASSERT_EQ(nodes, removed);
  ASSERT_FALSE(node.is_empty());
  validate("1 2 3 4 5 6 7 8", "8 7 6 5 4 3 2 1", &node);

  nodes[2].remove_this();
  ASSERT_FALSE(node.is_empty());
  validate("1 3 4 5 6 7 8", "8 7 6 5 4 3 1", &node);
}

}  // cc_shared
