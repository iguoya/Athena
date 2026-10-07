# microui 官方 demo：极简即时模式（rxi/microui，~1100 行核心）。
# 源码 vendor 于 third_party/microui/（src 核心与 demo SDL_Renderer 后端），
# SDL include 已就地修正为平铺形式。
add_executable(microui-demo
  ${CMAKE_SOURCE_DIR}/third_party/microui/demo/main.c
  ${CMAKE_SOURCE_DIR}/third_party/microui/demo/renderer.c
  ${CMAKE_SOURCE_DIR}/third_party/microui/src/microui.c)

find_package(PkgConfig REQUIRED)
pkg_check_modules(SDL2 REQUIRED sdl2)
target_include_directories(microui-demo PRIVATE
  ${SDL2_INCLUDE_DIRS}
  ${CMAKE_SOURCE_DIR}/third_party/microui/src
  ${CMAKE_SOURCE_DIR}/third_party/microui/demo)
target_link_directories(microui-demo PRIVATE ${SDL2_LIBRARY_DIRS})
# GNU ld 在本机会因杀软扫描丢错误甚至静默失败，lld 行为确定
target_link_options(microui-demo PRIVATE -fuse-ld=lld)
target_link_libraries(microui-demo PRIVATE ${SDL2_LIBRARIES} opengl32)
