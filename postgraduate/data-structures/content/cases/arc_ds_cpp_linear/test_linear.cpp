#include <gtest/gtest.h>
#include "linear.h"

TEST(push_back, Linear) {
    Linear<int> t;
    //测试空对象
    EXPECT_EQ(t.empty(), true);
    EXPECT_EQ(t.full(), true);
    //测试添加第一个对象
    t.push_back(222);
    EXPECT_EQ(t.capacity(), 1);
    EXPECT_EQ(*t.begin(), 222);
    EXPECT_EQ(t.full(), true);
    EXPECT_EQ(t.size(), 1);
    //测试添加多个对象
    t.push_back(666);
    t.push_back(999);
    size_t result[3] = {222, 666, 999};
    int i = 0;
    for(auto *pt = t.begin(); pt != t.end(); ++pt, ++i) {
         EXPECT_EQ(*pt, result[i]);
    }
    t.push_back(4);
    t.push_back(5);
    t.push_back(6);
     EXPECT_EQ(t.size(), 6);
     EXPECT_EQ(t.capacity(), 8);
}


int main(int argc, char *argv[])
{
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
