cmake_minimum_required(VERSION 2.8)

project(tree)
add_executable(${PROJECT_NAME} "main.cpp")



find_package(GTest REQUIRED)
find_package(Threads REQUIRED)
include_directories(${GTEST_INCLUDE_DIRS})

add_executable(test_btree test_btree.cpp)
target_link_libraries(test_btree ${GTEST_BOTH_LIBRARIES})
target_link_libraries(test_btree ${CMAKE_THREAD_LIBS_INIT})
add_test(Test test_btree)
