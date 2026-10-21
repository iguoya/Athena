#include <gtest/gtest.h>
#include <vector>
#include <string>
#include <iostream>
#include "btree.h"

using namespace std;

class BtreeTest: public ::testing::Test
{
public:
    Btree<string> tree;
    vector<string> result;
protected:
    // You can remove any or all of the following functions if its body
    // is empty.

    BtreeTest() {
        // You can do set-up work for each test here.
    }

    ~BtreeTest() override {
        // You can do clean-up work that doesn't throw exceptions here.
    }

    // If the constructor and destructor are not enough for setting up
    // and cleaning up each test, you can define the following methods:

    void SetUp() override {
        // Code here will be called immediately after the constructor (right
        // before each test).
        BtreeNode<string> *root = new BtreeNode<string>(new string("A"));
        root->add_child(new BtreeNode<string>(new string("B")), new BtreeNode<string>(new string("C")));
        root->lchild->add_child(new BtreeNode<string>(new string("D")), new BtreeNode<string>(new string("E")));
        root->rchild->add_child(new BtreeNode<string>(new string("F")), new BtreeNode<string>(new string("G")));
        tree.root=root;

    }

    void TearDown() override {
        // Code here will be called immediately after each test (right
        // before the destructor).
        result.clear();

    }
};
TEST_F(BtreeTest, DLR)   //此时使用的是TEST_F宏
{
    tree.DLR(tree.root, result);
    vector<string> dlr = {"A", "B", "D", "E", "C", "F", "G"};
    EXPECT_EQ(result, dlr);
}

TEST_F(BtreeTest, LDR)   //此时使用的是TEST_F宏
{
    tree.LDR(tree.root, result);
    vector<string> ldr = {"D", "B", "E", "A", "F", "C", "G"};
    EXPECT_EQ(result, ldr);
}

TEST_F(BtreeTest, DLRTraversal)   //此时使用的是TEST_F宏
{
    result = tree.DLRTraverse();
    vector<string> dlr = {"A", "B", "D", "E", "C", "F", "G"};
    EXPECT_EQ(result, dlr);
}

TEST_F(BtreeTest, LDRTraversal)   //此时使用的是TEST_F宏
{
    result = tree.LDRTraverse();
    vector<string> ldr = {"D", "B", "E", "A", "F", "C", "G"};
    EXPECT_EQ(result, ldr);
}

TEST_F(BtreeTest, LRD)   //此时使用的是TEST_F宏
{
    tree.LRD(tree.root, result);
    vector<string> lrd = {"D", "E", "B", "F", "G", "C", "A"};
    EXPECT_EQ(result, lrd);
}

TEST_F(BtreeTest, high)   //此时使用的是TEST_F宏
{
    EXPECT_EQ(tree.depth(tree.root), 3);
}

TEST_F(BtreeTest, LevelTraverse)   //此时使用的是TEST_F宏
{
    vector<string> result = {"A", "B", "C", "D", "E", "F", "G"};
    EXPECT_EQ(result, tree.LevelTraverse());
}



int main(int argc,char *argv[])
{
    testing::InitGoogleTest(&argc, argv);//将命令行参数传递给gtest
    return RUN_ALL_TESTS();   //RUN_ALL_TESTS()运行所有测试案例
}
