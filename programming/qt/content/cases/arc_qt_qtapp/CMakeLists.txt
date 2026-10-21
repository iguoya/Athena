cmake_minimum_required(VERSION 3.5)

project(QtApp LANGUAGES CXX)

set(CMAKE_INCLUDE_CURRENT_DIR ON)

set(CMAKE_AUTOUIC ON)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)

set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# QtCreator supports the following variables for Android, which are identical to qmake Android variables.
# Check https://doc.qt.io/qt/deployment-android.html for more information.
# They need to be set before the find_package( ...) calls below.

#if(ANDROID)
#    set(ANDROID_PACKAGE_SOURCE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/android")
#    if (ANDROID_ABI STREQUAL "armeabi-v7a")
#        set(ANDROID_EXTRA_LIBS
#            ${CMAKE_CURRENT_SOURCE_DIR}/path/to/libcrypto.so
#            ${CMAKE_CURRENT_SOURCE_DIR}/path/to/libssl.so)
#    endif()
#endif()

find_package(QT NAMES Qt6 Qt5 COMPONENTS Widgets REQUIRED)
find_package(Qt${QT_VERSION_MAJOR} COMPONENTS Widgets REQUIRED)


#qt5_add_resources(QRC_FILES ${CMAKE_CURRENT_SOURCE_DIR}/qdarkstyle/dark/style.qrc)
qt5_add_resources(themes ${CMAKE_CURRENT_SOURCE_DIR}/qdarkstyle/dark/style.qrc)
qt5_add_resources(images ${CMAKE_CURRENT_SOURCE_DIR}/resource.qrc)
#file(GLOB_RECURSE QRC_SOURCE_FILES ${CMAKE_CURRENT_SOURCE_DIR}/qdarkstyle/dark/style.qrc)
#set(QRC_SOURCE_FILES Resources.qrc)
#SOURCE_GROUP("Resource Files" FILES ${QRC_SOURCE_FILES})

set_target_properties(${TARGET} PROPERTIES
COMPILE_FLAGS "-pthread"
LINK_FLAGS "-pthread")


set(PROJECT_SOURCES
    main.cpp
    ${themes}
    ${images}
    mainwindow.cpp
    mainwindow.h
    mainwindow.ui
#    QtAwesome/QtAwesome.h
#    QtAwesome/QtAwesomeAnim.h
#    QtAwesome/QtAwesome.cpp
#    QtAwesome/QtAwesomeAnim.cpp
    system.h
    system.cpp
    system.ui
    thread.h
    thread.cpp
    thread.ui
    )

if(${QT_VERSION_MAJOR} GREATER_EQUAL 6)
    qt_add_executable(QtApp
        ${PROJECT_SOURCES}
        )
else()
    if(ANDROID)
        add_library(QtApp SHARED
            ${PROJECT_SOURCES}
            )
    else()
        add_executable(QtApp
            ${PROJECT_SOURCES}
            ${themes}
            ${images}
            )
    endif()
endif()

target_link_libraries(QtApp PRIVATE Qt${QT_VERSION_MAJOR}::Widgets pthread)
