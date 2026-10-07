set(IMGUI ${CMAKE_SOURCE_DIR}/third_party/imgui)

add_executable(imgui-style imgui_style.cpp
  ${IMGUI}/imgui.cpp
  ${IMGUI}/imgui_draw.cpp
  ${IMGUI}/imgui_tables.cpp
  ${IMGUI}/imgui_widgets.cpp
  ${IMGUI}/imgui_demo.cpp
  ${IMGUI}/backends/imgui_impl_win32.cpp
  ${IMGUI}/backends/imgui_impl_dx11.cpp)

target_include_directories(imgui-style PRIVATE ${IMGUI} ${IMGUI}/backends)
target_compile_definitions(imgui-style PRIVATE UNICODE _UNICODE)
target_link_libraries(imgui-style PRIVATE d3d11 dxgi d3dcompiler dwmapi)
