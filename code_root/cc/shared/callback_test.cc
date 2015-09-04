/*Unit tests for callback macros.*/
#include "cc/shared/callback.h"

#include "gtest/gtest.h"

#include <boost/atomic.hpp>

namespace cc_shared {

namespace {

class Context {
 public:
  Context() : field0_(0), field1_(0), field2_(0) {
  }

  ~Context() {
  }

  void callback_zero() {
    ++field0_;
  }

  void callback_one(boost::atomic<int>* param1) {
    CHECK_EQ(&field1_, param1);
    ++field1_;
  }

  void callback_two(boost::atomic<int>* param1,
                    boost::atomic<int>* param2) {
    CHECK_EQ(&field1_, param1);
    CHECK_EQ(&field2_, param2);
    ++field1_;
    ++field2_;
  }

  void validate(int val0, int val1, int val2) {
    CHECK(field0_ == val0);
    CHECK(field1_ == val1);
    CHECK(field2_ == val2);
  }

  boost::atomic<int>* get_field1() {
    return &field1_;
  }

  boost::atomic<int>* get_field2() {
    return &field2_;
  }

  static void set_static_context(Context* context) {
    static_context_ = context;
  }

  static void static_callback_zero() {
    static_context_->callback_zero();
  }

  static void static_callback_one(boost::atomic<int>* param1) {
    static_context_->callback_one(param1);
  }

  static void static_callback_two(boost::atomic<int>* param1,
                           boost::atomic<int>* param2) {
    static_context_->callback_two(param1, param2);
  }

 private:
  boost::atomic<int> field0_;
  boost::atomic<int> field1_;
  boost::atomic<int> field2_;
  static Context* static_context_;

  DISALLOW_COPY_AND_ASSIGN(Context);
};

Context* Context::static_context_ = NULL;

}  // namespace

TEST(CallbackTest, test_function) {
  Context context;
  Context::set_static_context(&context);
  context.validate(0, 0, 0);

  // Function callback with zero parameters.
  {
    Closure* callback0 = NewCallback(Context::static_callback_zero);
    callback0->Run();
  }
  context.validate(1, 0, 0);

  // Function callback with one parameter.
  {
    Closure* callback1 = NewCallback(
        Context::static_callback_one, context.get_field1());
    callback1->Run();
  }
  context.validate(1, 1, 0);

  // Function callback with two parameters.
  {
    Closure* callback2 = NewCallback(
        Context::static_callback_two, context.get_field1(),
        context.get_field2());
    callback2->Run();
  }
  context.validate(1, 2, 1);

  // Permanent callback.
  {
    Closure* permanent_callback2 = NewPermanentCallback(
        Context::static_callback_two, context.get_field1(),
        context.get_field2());
    permanent_callback2->Run();
    permanent_callback2->Run();
    delete permanent_callback2;
  }
  context.validate(1, 4, 3);
}

TEST(CallbackTest, test_method) {
  Context context;
  context.validate(0, 0, 0);

  // Method callback with zero parameters.
  {
    Closure* callback0 = NewCallback(
        &context, &Context::callback_zero);
    callback0->Run();
  }
  context.validate(1, 0, 0);

  // Method callback with one parameter.
  {
    Closure* callback1 = NewCallback(
        &context, &Context::callback_one, context.get_field1());
    callback1->Run();
  }
  context.validate(1, 1, 0);

  // Method callback with two parameters.
  {
    Closure* callback2 = NewCallback(
        &context, &Context::callback_two, context.get_field1(),
        context.get_field2());
    callback2->Run();
  }
  context.validate(1, 2, 1);

  // Permanent callback.
  {
    Closure* permanent_callback2 = NewPermanentCallback(
        &context, &Context::callback_two, context.get_field1(),
        context.get_field2());
    permanent_callback2->Run();
    permanent_callback2->Run();
    permanent_callback2->Run();
    delete permanent_callback2;
  }
  context.validate(1, 5, 4);
}

}  // cc_shared
