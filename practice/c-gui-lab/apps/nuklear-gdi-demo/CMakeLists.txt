# Nuklear GDI 原生演示（demo/gdi_native_nuklear）：纯 Win32 GDI 渲染，
# 不依赖 SDL/OpenGL，展示同一套 Nuklear 控件在原生窗口框架下的样子。
# 源码 vendor 于 third_party/nuklear_gdi/（include 已就地修正）。
add_executable(nuklear-gdi-demo WIN32
  ${CMAKE_SOURCE_DIR}/third_party/nuklear_gdi/main.c)

target_include_directories(nuklear-gdi-demo PRIVATE
  ${CMAKE_SOURCE_DIR}/third_party
  ${CMAKE_SOURCE_DIR}/third_party/nuklear_gdi)
target_compile_definitions(nuklear-gdi-demo PRIVATE UNICODE _UNICODE)
# wWinMain 入口要 -municode；AlphaBlend 在 msimg32；lld 链接器（同 microui-demo）
target_link_options(nuklear-gdi-demo PRIVATE -fuse-ld=lld -municode)
target_link_libraries(nuklear-gdi-demo PRIVATE user32 gdi32 msimg32)
# 同 microui-demo：lld 链接器
target_link_options(nuklear-gdi-demo PRIVATE -fuse-ld=lld)
