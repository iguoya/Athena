cmake_minimum_required(VERSION 3.5)

project(5-image LANGUAGES C)

#add_executable(5-image main.c)

find_package(SDL2 REQUIRED)
include_directories(${SDL2_INCLUDE_DIRS})
configure_file(redflag.bmp redflag.bmp COPYONLY)

add_executable(5-image main.c)


target_link_libraries(5-image ${SDL2_LIBRARIES})
