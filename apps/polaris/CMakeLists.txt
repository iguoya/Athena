cmake_minimum_required(VERSION 3.22)
project(Polaris VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# app.json 的 `run`/`binary` 写死 build/athena-polaris（单配置生成器的扁平布局）。
# Windows 上 CMake 有时选中 Visual Studio 这种多配置生成器，产物会落进
# build/Debug/athena-polaris.exe，路径就对不上——这里强制所有配置都落回 build/ 顶层，
# 生成器选哪个都不影响 app.json 找得到它。
foreach(_config_type ${CMAKE_CONFIGURATION_TYPES})
    string(TOUPPER "${_config_type}" _config_upper)
    set(CMAKE_RUNTIME_OUTPUT_DIRECTORY_${_config_upper} "${CMAKE_BINARY_DIR}")
endforeach()
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}")

find_package(Qt6 6.5 REQUIRED COMPONENTS Core Gui Quick Qml QuickControls2 Network Svg Test)

add_library(polaris_domain STATIC
    src/polaris_catalog.cpp
)
target_include_directories(polaris_domain PUBLIC src)
target_link_libraries(polaris_domain PUBLIC Qt6::Core)

# 壳层：保证同一时刻只有一个 Polaris 进程。单独成库，内容校验的测试才能继续不依赖
# GUI 和网络，而这条守卫本身也能被测到。
add_library(polaris_shell STATIC
    src/single_instance.cpp
)
target_include_directories(polaris_shell PUBLIC src)
target_link_libraries(polaris_shell PUBLIC Qt6::Gui Qt6::Network)

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
# 道理）。polaris_domain_tests/polaris_shell_tests 两个测试可执行文件不加——
# 测试要往标准输出打结果，需要控制台。
qt_add_executable(athena-polaris WIN32
    src/main.cpp
    ${windows_resource}
)
target_link_libraries(athena-polaris PRIVATE polaris_domain polaris_shell Qt6::Quick Qt6::Qml Qt6::QuickControls2 Qt6::Svg)
target_compile_definitions(athena-polaris PRIVATE POLARIS_SOURCE_ROOT="${CMAKE_SOURCE_DIR}")

qt_add_executable(polaris_domain_tests
    tests/polaris_catalog_test.cpp
)
target_link_libraries(polaris_domain_tests PRIVATE polaris_domain Qt6::Test)
target_compile_definitions(polaris_domain_tests PRIVATE POLARIS_SOURCE_ROOT="${CMAKE_SOURCE_DIR}")

qt_add_executable(polaris_shell_tests
    tests/polaris_shell_test.cpp
)
target_link_libraries(polaris_shell_tests PRIVATE polaris_shell Qt6::Test)

if(APPLE)
    # 开发阶段直接运行 build/athena-polaris，也能找到 Homebrew 的 Qt 动态库。
    get_filename_component(_qt_prefix "${Qt6_DIR}/../../.." ABSOLUTE)
    set_target_properties(athena-polaris PROPERTIES BUILD_RPATH "${_qt_prefix}/lib")
endif()

enable_testing()
add_test(NAME polaris_domain_tests COMMAND polaris_domain_tests)
add_test(NAME polaris_shell_tests COMMAND polaris_shell_tests)

# 单个测试秒级跑完；给个上限，挂住时两分钟内报错，而不是耗光整个 CI job。
set_tests_properties(polaris_domain_tests polaris_shell_tests PROPERTIES TIMEOUT 120)

if(WIN32)
    # Windows 按 PATH 找 DLL，而 aqt / 官方安装器装的 Qt 不在 PATH 上。缺 DLL 时
    # 系统弹模态框等人点，ctest 会一直挂到 job 超时——CI 上北极星的 Windows job
    # 次次 45 分钟被取消就是这个。测试时把 Qt 的 bin 目录前插进 PATH。
    set_tests_properties(polaris_domain_tests polaris_shell_tests PROPERTIES
        ENVIRONMENT_MODIFICATION "PATH=path_list_prepend:$<TARGET_FILE_DIR:Qt6::Core>")
endif()
