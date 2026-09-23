cmake_minimum_required(VERSION 3.20)
project(AthenaC VERSION 0.1.0 LANGUAGES CXX)

# Qt Quick 教学应用（ADR 0042）。主程序 Meson 不引用本目录。
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# app.json 的 `run`/`binary` 写死 build/athena-c（单配置生成器的扁平布局）。
# Windows 上 CMake 有时选中 Visual Studio 这种多配置生成器，产物会落进
# build/Debug/athena-c.exe，路径就对不上——这里强制所有配置都落回 build/ 顶层，
# 生成器选哪个都不影响 app.json 找得到它。
foreach(_config_type ${CMAKE_CONFIGURATION_TYPES})
    string(TOUPPER "${_config_type}" _config_upper)
    set(CMAKE_RUNTIME_OUTPUT_DIRECTORY_${_config_upper} "${CMAKE_BINARY_DIR}")
endforeach()
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}")

find_package(Qt6 6.5 REQUIRED COMPONENTS Quick Qml Svg)

# Windows 文件属性（右键属性 -> 详细信息）：CMake/Qt 构建的可执行文件默认没有
# 这份信息，Tauri/Flutter 的打包器会自动生成，这里手动补齐（不含图标——标题栏
# 和任务栏图标已经在 main.cpp 里用 QIcon 运行时设置，见 app.setWindowIcon）。
set(windows_resource "")
if(WIN32)
    set(VERSION_STR "${PROJECT_VERSION}")
    set(VERSION_COMMA "${PROJECT_VERSION_MAJOR},${PROJECT_VERSION_MINOR},${PROJECT_VERSION_PATCH},0")
    set(app_rc "${CMAKE_CURRENT_BINARY_DIR}/app.rc")
    configure_file(packaging/windows/app.rc.in "${app_rc}" @ONLY)
    set(windows_resource "${app_rc}")
endif()

# WIN32：Windows 上链接成 GUI 子系统，不带控制台窗口。不加这个，直接双击
# exe 或者被脚本拉起时都会先弹一个黑色控制台窗口再显示真正的界面。
# 其它平台忽略这个关键字，不用另外分支。
qt_add_executable(athena-c WIN32
    src/main.cpp
    src/curriculum.cpp
    src/reloader.cpp
    ${windows_resource}
)

target_include_directories(athena-c PRIVATE src)
target_link_libraries(athena-c PRIVATE Qt6::Quick Qt6::Qml Qt6::Svg)
target_compile_definitions(athena-c PRIVATE
    ATHENA_C_SOURCE_ROOT="${CMAKE_SOURCE_DIR}")

if(APPLE)
    # 开发时直接跑 build/athena-c，让它能找到 Homebrew 的 Qt。
    get_filename_component(_qt_prefix "${Qt6_DIR}/../../.." ABSOLUTE)
    set_target_properties(athena-c PROPERTIES
        BUILD_RPATH "${_qt_prefix}/lib")
endif()
