cmake_minimum_required(VERSION 3.24)
project(c-gui-lab C CXX)

# 三个框架各一个样式测试程序，互不依赖，可单独构建。
add_subdirectory(apps/gtk-style)
add_subdirectory(apps/imgui-style)
add_subdirectory(apps/lvgl-style)
# 官方控件合集演示：raygui 与 Nuklear 的即时代码没有自研橱窗，直接编译官方 demo。
add_subdirectory(apps/raygui-demo)
add_subdirectory(apps/nuklear-demo)
add_subdirectory(apps/nuklear-gdi-demo)
add_subdirectory(apps/microui-demo)
