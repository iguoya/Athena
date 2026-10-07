# Nuklear 官方 SDL2/OpenGL2 演示：单头文件库 + 官方 demo main.c。
# 源码 vendor 于 third_party/（Immediate-Mode-UI/Nuklear@master），
# include 已就地修正为平铺结构。
add_executable(nuklear-demo ${CMAKE_SOURCE_DIR}/third_party/nuklear_sdl2.c)

find_package(PkgConfig REQUIRED)
pkg_check_modules(SDL2 REQUIRED sdl2)
target_include_directories(nuklear-demo PRIVATE ${SDL2_INCLUDE_DIRS}
                                                ${CMAKE_SOURCE_DIR}/third_party)
target_link_directories(nuklear-demo PRIVATE ${SDL2_LIBRARY_DIRS})
target_link_libraries(nuklear-demo PRIVATE ${SDL2_LIBRARIES} opengl32)
