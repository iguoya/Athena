cmake_minimum_required(VERSION 3.20)
project(AthenaC VERSION 0.1.0 LANGUAGES CXX)

# Qt Quick 教学应用（ADR 0042）。主程序 Meson 不引用本目录。
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

find_package(Qt6 6.5 REQUIRED COMPONENTS Quick Qml)

qt_add_executable(athena-c
    src/main.cpp
    src/curriculum.cpp
    src/reloader.cpp
)

target_include_directories(athena-c PRIVATE src)
target_link_libraries(athena-c PRIVATE Qt6::Quick Qt6::Qml)
target_compile_definitions(athena-c PRIVATE
    ATHENA_C_SOURCE_ROOT="${CMAKE_SOURCE_DIR}")

if(APPLE)
    # 开发时直接跑 build/athena-c，让它能找到 Homebrew 的 Qt。
    get_filename_component(_qt_prefix "${Qt6_DIR}/../../.." ABSOLUTE)
    set_target_properties(athena-c PROPERTIES
        BUILD_RPATH "${_qt_prefix}/lib")
endif()
