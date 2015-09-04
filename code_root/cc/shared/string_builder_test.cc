/*Unit tests for string builder module.*/
#include "cc/shared/string_builder.h"

#include "gtest/gtest.h"

namespace cc_shared {

namespace {

void test_loop(const char* text, int loop_count) {
  BufferBuilder builder;
  int text_length = strlen(text);
  for (int i = 0; i < loop_count; ++i) {
    builder.append(text, text_length);
  }
  builder.append_null_terminator();
  BufferBuilder::BufferInfo info = builder.get();
  CHECK_EQ(0, info.ptr[info.length - 1]);
  CHECK_EQ(static_cast<int>(1 + strlen(info.ptr)), info.length);
  CHECK_EQ(loop_count * text_length, info.length - 1);
  const char* built = info.ptr;
  const char* current = built;
  for (int i = 0; i < loop_count; ++i) {
    for (int j = 0; j < text_length; ++j) {
      CHECK_EQ(current[j], text[j]);
    }
    current += text_length;
  }
  CHECK_EQ(current[0], 0);
}

}  // namespace


TEST(BufferBuilderTest, test_append_c_str) {
  static const char* kText = "Mary had a little lamb.";
  BufferBuilder builder;
  builder.append_c_str(kText);
  builder.append_null_terminator();
  EXPECT_STREQ(kText, builder.get().ptr);
  EXPECT_EQ(1 + strlen(kText), builder.get().length);
}

TEST(StringBuilderTest, test_simple) {
  static const char* kInput = "ABCDEFGHIJ";
  static const char* kExpected = "ABCDEFGHIJABCDEFGHIJ";
  StringBuilder builder;
  builder.append_c_str(kInput);
  builder.append_c_str(kInput);
  EXPECT_STREQ(kExpected, builder.c_str());
}

TEST(StringBuilderTest, test_null_terminator_added) {
  StringBuilder builder;
  char text[2];
  text[0] = text[1] = 'a';
  builder.append(text, 2);
  builder.append(text, 2);
  EXPECT_EQ(4, strlen(builder.c_str()));
  EXPECT_EQ(4, builder.get_str_len());
}

TEST(BufferBuilderTest, test_small_buffer_many_chunks) {
  static const char* kText = "I wish you a Merry Christmas.";
  test_loop(kText, 0);
  test_loop(kText, 103);
  test_loop(kText, 999);
  test_loop(kText, 345678);
}

TEST(BufferBuilderTest, test_large_buffer_few_chunks) {
  // First build a large buffer.
  static const char* kText = "Thats all that is there to it.";
  const int text_length = strlen(kText);
  BufferBuilder large_builder;
  int large_builder_len = 0;
  while (large_builder_len < 10000) {
    large_builder.append(kText, text_length);
    large_builder_len += text_length;
  }
  large_builder.append_null_terminator();
  EXPECT_EQ(1 + strlen(large_builder.get().ptr), large_builder.get().length);
  for (int i = 0; i <= 10; ++i) {
    test_loop(large_builder.get().ptr, i);
  }
}

TEST(BufferBuilderTest, test_big_buffer_perf) {
  static const char* kText = "Thats all that is there to it.";
  const int text_length = strlen(kText);
  BufferBuilder builder;
  int builder_len = 0;
  while (builder_len < 10000) {
    builder.append(kText, text_length);
    builder_len += text_length;
  }
  builder.append_null_terminator();

  // This is a performance test, so verifications are disabled. We just add to
  // the builder and retrieve the pointer at the end.
  static const int kIterations = 100;
  static const int kMinimumSize = 100000;
  const char* read_ptr = builder.get().ptr;
  int read_len = builder.get().length - 1;
  int appends_needed = 1 + (100000 / read_len);
  int64 start_milli = get_epoch_milliseconds();
  for (int i = 0; i < kIterations; ++i) {
    BufferBuilder big_builder;
    for (int j = 0; j < appends_needed; ++j) {
      big_builder.append(read_ptr, read_len);
    }
    big_builder.append_null_terminator();
    // Access the constructed string to make sure it is available.
    CHECK_NE(NULL, big_builder.get().ptr);
    CHECK_LT(kMinimumSize, big_builder.get().length);
  }
  int64 stop_milli = get_epoch_milliseconds();
  LOG(INFO) << "Approximate processing time for building a 100K buffer is "
            << ((stop_milli - start_milli) * 1.0 / kIterations)
            << " milliseconds";
}

}  // cc_shared
