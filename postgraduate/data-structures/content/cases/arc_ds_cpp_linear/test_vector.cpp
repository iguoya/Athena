#include <gtest/gtest.h>
#include <numeric>
#include <vector>
using std::vector;

TEST(vector_accmulate, Vector)
{
    vector<int> vec{1, 2, 3, 4, 5};
    int sum = std::accumulate(vec.begin(), vec.end(), 0);
    EXPECT_EQ(sum, 15);
}

TEST(point, New) {
    int *p = new int(10);
    int *q = p;
    EXPECT_EQ(*p, *q);
    delete p;
    p = new int(100);

}
TEST(vector_push_back, Vector)
{
    vector<int> ivec4;
    EXPECT_EQ(ivec4.size(), 0);

    int x = 3;
    ivec4.push_back(x);
    EXPECT_EQ(ivec4.at(0), 3);
    auto it = ivec4.begin();
    EXPECT_EQ(*it, x);
}


TEST(vector_capacity, Vector)
{
    vector<int> ivec;
    for(int i = 1; i <= 100; ++i) {
        ivec.push_back(i);
    }
    EXPECT_EQ(ivec.size(), 100);
    EXPECT_EQ(ivec.capacity(), 128);

    ivec.clear();

    EXPECT_EQ(ivec.size(), 0);
    EXPECT_EQ(ivec.capacity(), 128);

    vector <int>().swap(ivec);

    EXPECT_EQ(ivec.size(), 0);
    EXPECT_EQ(ivec.capacity(), 0);

    vector<int> ivec2(200);
    EXPECT_EQ(ivec2.size(), 200);
    EXPECT_EQ(ivec2.capacity(), 200);

    vector<int> ivec3;
    for(int i = 1; i <= 300; ++i) {
        ivec3.push_back(i);
    }
    EXPECT_EQ(ivec3.size(), 300);
    EXPECT_EQ(ivec3.capacity(), 512);

    vector<int> ivec4;
    ivec4.reserve(2000);
    EXPECT_EQ(ivec4.capacity(), 2000);
    EXPECT_EQ(ivec4.size(), 0);

    vector<int> ivec5(2000);
    EXPECT_EQ(ivec5.capacity(), 2000);
    EXPECT_EQ(ivec5.size(), 2000);

    vector<int> ivec6;
    ivec6.push_back(666);
    EXPECT_EQ(ivec6.size(), 1);
    EXPECT_EQ(ivec6.capacity(), 1);
    ivec6.push_back(999);
    EXPECT_EQ(ivec6.size(), 2);
    EXPECT_EQ(ivec6.capacity(), 2);
    ivec6.push_back(333);
    EXPECT_EQ(ivec6.size(), 3);
    EXPECT_EQ(ivec6.capacity(), 4);
}

int main(int argc, char *argv[])
{
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
