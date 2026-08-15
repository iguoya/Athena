project(c++
#    VERSION 1.0
    DESCRIPTION "c++ 专项练习"
    LANGUAGES CXX
) #设置工程名

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
#set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++20")
SET (CMAKE_CXX_FLAGS                "-Wall")

find_package(PkgConfig REQUIRED)
pkg_check_modules(GTKMM REQUIRED gtkmm-3.0)
#pkg_check_modules(SIGCPP REQUIRED sigc++-2.0)
#pkg_check_modules(GLIB REQUIRED glib-2.0)
#include_directories(
#    ${GLIB_INCLUDE_DIRS}
#    ${SIGCPP_INCLUDE_DIRS}
#    ${GTKMM_INCLUDE_DIRS}
#    )
include_directories(${GTKMM_INCLUDE_DIRS})
link_directories(${GTKMM_LIBRARY_DIRS})
message("${GTKMM_INCLUDE_DIRS}")
# find_package(Boost REQUIRED COMPONENTS)
# include_directories(${Boost_INCLUDE_DIR})

include_directories(framework/)
include_directories(keyword/)

#list(
#    APPEND CMAKE_MODULE_PATH
#    ${CMAKE_CURRENT_SOURCE_DIR}/macros
#    )
#include(GlibCompileResourcesSupport)
#set(
#    RESOURCE_LIST
#    style.css
#    window.glade
#    )
#compile_gresources(RESOURCE_FILE XML_OUT TYPE EMBED_C RESOURCES ${RESOURCE_LIST} SOURCE_DIR ${CMAKE_CURRENT_SOURCE_DIR}/assets)


add_executable(c++
    main.cpp
    application.cpp
    mainwindow.cpp
    menumodel.cpp
    framework/product.cpp
    framework/singleton.cpp
    framework/factory.cpp
    basic/limits.cpp
    basic/define.cpp
    basic/pointer.cpp
    basic/getline.cpp
    basic/random.cpp
    basic/time.cpp
    keyword/keyword.cpp
    keyword/auto.cpp
    keyword/const.cpp
    keyword/nullptr.cpp
    keyword/tuple.cpp
    keyword/decltype.cpp

#    ${RESOURCE_FILE}
    )
target_link_libraries(c++ ${GTKMM_LIBRARIES} ${Boost_LIBRARIES} )
#target_compile_options(c++ PRIVATE ${GTKMM_CFLAGS_OTHER})
#target_link_libraries(
#    c++
#    ${SIGCPP_LIBRARIES}
#    ${GTKMM_LIBRARIES}
#    ${GLIB_LDFLAGS}
#    )
file(COPY window.glade DESTINATION ${CMAKE_CURRENT_BINARY_DIR})






