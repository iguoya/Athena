#include <gtest/gtest.h>
#include "list.h"



TEST(list_push_back, Add) {
//    ASSERT_EQ(4, 6);
    List<int> t;
    ASSERT_EQ(t.size(), 0);
    t.push_back(333);
    ASSERT_EQ(t.size(), 1);
    t.push_back(234);
    t.push_back(55);

    int result[3] = {333, 234, 55};
    int i = 0;
    for(auto it = t.begin(); it != t.end();  ++i) {
        ASSERT_EQ(it->data, result[i]);
        it = it->next;
    }
}




int main(int argc, char *argv[])
{
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
