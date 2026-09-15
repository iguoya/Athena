cmake_minimum_required(VERSION 3.20)
project(Atlas VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

find_package(Qt6 6.5 REQUIRED COMPONENTS Core Gui Quick Qml Network Test)

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

qt_add_executable(atlas
    src/main.cpp
)
target_link_libraries(atlas PRIVATE atlas_domain atlas_shell Qt6::Quick Qt6::Qml)
target_compile_definitions(atlas PRIVATE ATLAS_SOURCE_ROOT="${CMAKE_SOURCE_DIR}")

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
    # 开发阶段直接运行 build/atlas，也能找到 Homebrew 的 Qt 动态库。
    get_filename_component(_qt_prefix "${Qt6_DIR}/../../.." ABSOLUTE)
    set_target_properties(atlas PROPERTIES BUILD_RPATH "${_qt_prefix}/lib")
endif()

enable_testing()
add_test(NAME atlas_domain_tests COMMAND atlas_domain_tests)
add_test(NAME atlas_shell_tests COMMAND atlas_shell_tests)
