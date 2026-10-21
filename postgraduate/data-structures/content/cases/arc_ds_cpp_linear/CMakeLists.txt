cmake_minimum_required(VERSION 2.8)

project(linear)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -g -std=c++11 -Wall")
INCLUDE_DIRECTORIES("${PROJECT_SOURCE_DIR}")
add_executable(${PROJECT_NAME} "main.cpp")


find_package(GTest REQUIRED)
find_package(Threads REQUIRED)
include_directories(${GTEST_INCLUDE_DIRS})

add_executable(test_linear test_linear.cpp)
target_link_libraries(test_linear ${GTEST_BOTH_LIBRARIES})
target_link_libraries(test_linear ${CMAKE_THREAD_LIBS_INIT})
add_test(Test test_linear)

add_executable(test_vector test_vector.cpp)
target_link_libraries(test_vector ${GTEST_BOTH_LIBRARIES})
target_link_libraries(test_vector ${CMAKE_THREAD_LIBS_INIT})
add_test(Test test_vector)


add_executable(test_list test_list.cpp)
target_link_libraries(test_list ${GTEST_BOTH_LIBRARIES})
target_link_libraries(test_list ${CMAKE_THREAD_LIBS_INIT})
add_test(Test test_list)


add_executable(test_map test_map.cpp)
target_link_libraries(test_map ${GTEST_BOTH_LIBRARIES})
target_link_libraries(test_map ${CMAKE_THREAD_LIBS_INIT})
add_test(Test test_map)

enable_testing()
