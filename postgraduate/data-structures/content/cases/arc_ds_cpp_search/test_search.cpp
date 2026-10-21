#include <gtest/gtest.h>
#include <vector>
#include <string>
#include <iostream>
#include "search.h"

using namespace std;

class SearchTest: public ::testing::Test
{
public:
    Search<int> normal;
    Search<int> order;
protected:
    // You can remove any or all of the following functions if its body
    // is empty.

    SearchTest() {
        // You can do set-up work for each test here.
        normal.data = {10, 15, 24, 6, 12, 35, 40, 98, 55};
        order.data = {2, 7, 11, 31, 37, 46, 55, 63, 73};
    }

    ~SearchTest() override {
        // You can do clean-up work that doesn't throw exceptions here.
    }

    // If the constructor and destructor are not enough for setting up
    // and cleaning up each test, you can define the following methods:

    void SetUp() override {
        // Code here will be called immediately after the constructor (right
        // before each test).

    }

    void TearDown() override {
        // Code here will be called immediately after each test (right
        // before the destructor).


    }
};
TEST_F(SearchTest, Sequence)   //此时使用的是TEST_F宏
{

    EXPECT_EQ(normal.sequence(new int(12)), 5);
    EXPECT_EQ(normal.sequence(new int(10)), 1);
    EXPECT_EQ(normal.sequence(new int(55)), 9);
    EXPECT_EQ(normal.sequence(new int(13)), 0);
}

TEST_F(SearchTest, InOrder)   //此时使用的是TEST_F宏
{
    EXPECT_EQ(order.binary(new int(63)), 8);
    EXPECT_EQ(order.binary(new int(2)), 1);
    EXPECT_EQ(order.binary(new int(73)), 9);
    EXPECT_EQ(order.binary(new int(4)), 0);
}




int main(int argc,char *argv[])
{
    testing::InitGoogleTest(&argc, argv);//将命令行参数传递给gtest
    return RUN_ALL_TESTS();   //RUN_ALL_TESTS()运行所有测试案例
}
