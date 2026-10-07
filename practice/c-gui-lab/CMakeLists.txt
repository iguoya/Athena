cmake_minimum_required(VERSION 3.24)
project(c-gui-lab C CXX)

# 三个框架各一个样式测试程序，互不依赖，可单独构建。
add_subdirectory(apps/gtk-style)
add_subdirectory(apps/imgui-style)
add_subdirectory(apps/lvgl-style)
