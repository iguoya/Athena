cmake_minimum_required(VERSION 3.5)

project(Algorithm LANGUAGES CXX)

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
include_directories (Abstract)
include_directories (Exhaustion)
include_directories (Deduction)
include_directories (Recursion)
include_directories (DivideConquer)

aux_source_directory(Abstract Abstract)
aux_source_directory(Exhaustion Exhaustion)
aux_source_directory(Deduction Deduction)
aux_source_directory(Recursion Recursion)
aux_source_directory(DivideConquer DivideConquer)

#qt5_add_resources(images ${CMAKE_CURRENT_SOURCE_DIR}/resource.qrc)

find_package(QT NAMES Qt6 Qt5 COMPONENTS Widgets REQUIRED)
find_package(Qt${QT_VERSION_MAJOR} COMPONENTS Widgets REQUIRED)


qt5_add_resources(themes ${CMAKE_CURRENT_SOURCE_DIR}/qdarkstyle/dark/darkstyle.qrc)
#qt5_add_resources(images ${CMAKE_CURRENT_SOURCE_DIR}/resource.qrc)



set(PROJECT_SOURCES
        main.cpp
        mainwindow.cpp
        mainwindow.h
        mainwindow.ui
        ${themes}
        ${Abstract}
        ${Exhaustion}
        ${Recursion}
        ${Deduction}
        ${DivideConquer}
#        ${images}

)

if(${QT_VERSION_MAJOR} GREATER_EQUAL 6)
    qt_add_executable(Algorithm
        ${PROJECT_SOURCES}
    )
else()
    if(ANDROID)
        add_library(Algorithm SHARED
            ${PROJECT_SOURCES}
        )
    else()
        add_executable(Algorithm
            ${PROJECT_SOURCES}
            ${themes}
#            ${images}
        )
    endif()
endif()

target_link_libraries(Algorithm PRIVATE Qt${QT_VERSION_MAJOR}::Widgets)
