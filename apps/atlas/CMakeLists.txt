cmake_minimum_required(VERSION 3.20)
project(Atlas VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# app.json 的 `run`/`binary` 写死 build/athena-atlas（单配置生成器的扁平布局）。
# Windows 上 CMake 有时选中 Visual Studio 这种多配置生成器，产物会落进
# build/Debug/athena-atlas.exe，路径就对不上——这里强制所有配置都落回 build/ 顶层，
# 生成器选哪个都不影响 app.json 找得到它。
foreach(_config_type ${CMAKE_CONFIGURATION_TYPES})
    string(TOUPPER "${_config_type}" _config_upper)
    set(CMAKE_RUNTIME_OUTPUT_DIRECTORY_${_config_upper} "${CMAKE_BINARY_DIR}")
endforeach()
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}")

find_package(Qt6 6.5 REQUIRED COMPONENTS Core Gui Quick Qml QuickControls2 Network Svg Test)

add_library(atlas_domain STATIC
    src/atlas_catalog.cpp
)
target_include_directories(atlas_domain PUBLIC src)
target_link_libraries(atlas_domain PUBLIC Qt6::Core)

# 壳层：保证同一时刻只有一个 Atlas 进程。单独成库，内容校验的测试才能继续不依赖
# GUI 和网络，而这条守卫本身也能被测到。
add_library(atlas_shell STATIC
    src/single_instance.cpp
)
target_include_directories(atlas_shell PUBLIC src)
target_link_libraries(atlas_shell PUBLIC Qt6::Gui Qt6::Network)

# Windows 文件属性（右键属性 -> 详细信息）：CMake/Qt 构建的可执行文件默认没有
# 这份信息，Tauri/Flutter 的打包器会自动生成，这里手动补齐（不含图标——标题栏
# 和任务栏图标已经在 main.cpp 里用 QIcon 运行时设置，见 application.setWindowIcon）。
set(windows_resource "")
if(WIN32)
    set(VERSION_STR "${PROJECT_VERSION}")
    set(VERSION_COMMA "${PROJECT_VERSION_MAJOR},${PROJECT_VERSION_MINOR},${PROJECT_VERSION_PATCH},0")
    set(app_rc "${CMAKE_CURRENT_BINARY_DIR}/app.rc")
    configure_file(packaging/windows/app.rc.in "${app_rc}" @ONLY)
    set(windows_resource "${app_rc}")
endif()

# WIN32：Windows 上链接成 GUI 子系统，不带控制台窗口（跟 apps/c 同一个
# 道理）。atlas_domain_tests/atlas_shell_tests 两个测试可执行文件不加——
# 测试要往标准输出打结果，需要控制台。
qt_add_executable(athena-atlas WIN32
    src/main.cpp
    ${windows_resource}
)
target_link_libraries(athena-atlas PRIVATE atlas_domain atlas_shell Qt6::Quick Qt6::Qml Qt6::QuickControls2 Qt6::Svg)
target_compile_definitions(athena-atlas PRIVATE ATLAS_SOURCE_ROOT="${CMAKE_SOURCE_DIR}")

qt_add_executable(atlas_domain_tests
    tests/atlas_catalog_test.cpp
)
target_link_libraries(atlas_domain_tests PRIVATE atlas_domain Qt6::Test)
target_compile_definitions(atlas_domain_tests PRIVATE ATLAS_SOURCE_ROOT="${CMAKE_SOURCE_DIR}")

qt_add_executable(atlas_shell_tests
    tests/atlas_shell_test.cpp
)
target_link_libraries(atlas_shell_tests PRIVATE atlas_shell Qt6::Test)

if(APPLE)
    # 开发阶段直接运行 build/athena-atlas，也能找到 Homebrew 的 Qt 动态库。
    get_filename_component(_qt_prefix "${Qt6_DIR}/../../.." ABSOLUTE)
    set_target_properties(athena-atlas PROPERTIES BUILD_RPATH "${_qt_prefix}/lib")
endif()

enable_testing()
add_test(NAME atlas_domain_tests COMMAND atlas_domain_tests)
add_test(NAME atlas_shell_tests COMMAND atlas_shell_tests)
