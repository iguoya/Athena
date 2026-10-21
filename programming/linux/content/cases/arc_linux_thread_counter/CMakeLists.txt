cmake_minimum_required(VERSION 3.5)

project(T03-Mutex LANGUAGES C)


find_package (Threads)
add_executable(T03-Mutex main.c)
target_link_libraries (T03-Mutex ${CMAKE_THREAD_LIBS_INIT})
