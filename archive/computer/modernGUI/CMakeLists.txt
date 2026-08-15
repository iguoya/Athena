# cmake_minimum_required(VERSION 3.5)

# project(modernGUI LANGUAGES CXX)

# set(CMAKE_INCLUDE_CURRENT_DIR ON)

# set(CMAKE_AUTOUIC ON)
# set(CMAKE_AUTOMOC ON)
# set(CMAKE_AUTORCC ON)

# set(CMAKE_CXX_STANDARD 17)
# set(CMAKE_CXX_STANDARD_REQUIRED ON)

# # QtCreator supports the following variables for Android, which are identical to qmake Android variables.
# # Check http://doc.qt.io/qt-5/deployment-android.html for more information.
# # They need to be set before the find_package(Qt5 ...) call.

# #if(ANDROID)
# #    set(ANDROID_PACKAGE_SOURCE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/android")
# #    if (ANDROID_ABI STREQUAL "armeabi-v7a")
# #        set(ANDROID_EXTRA_LIBS
# #            ${CMAKE_CURRENT_SOURCE_DIR}/path/to/libcrypto.so
# #            ${CMAKE_CURRENT_SOURCE_DIR}/path/to/libssl.so)
# #    endif()
# #endif()

# find_package(Qt6 6.4 COMPONENTS Core Quick QuickControls2 REQUIRED)

# qt_standard_project_setup()

# if(ANDROID)
#     add_library(modernGUI SHARED
#       main.cpp
#       qml.qrc
#     )
# else()
#     add_executable(modernGUI
#       main.cpp
#       Bridge/car.cpp
#       Bridge/audicar.cpp
#       Bridge/benzcar.cpp
# #      Bridge/bev.cpp
#       Bridge/bmwcar.cpp
# #      Bridge/iceengine.cpp
#       Bridge/engine.cpp
#       Bridge/fuelengine.cpp
#       Bridge/hybridengine.cpp
#       Bridge/electricengine.cpp
#       Bridge/bridge.cpp
#       Bridge/bridge.qmodel
#       qml.qrc
#     )
# endif()

# target_compile_definitions(modernGUI
#   PRIVATE $<$<OR:$<CONFIG:Debug>,$<CONFIG:RelWithDebInfo>>:QT_QML_DEBUG>)
# target_link_libraries(modernGUI
#   PRIVATE Qt6::Core Qt6::Quick Qt6::QuickControls2)


cmake_minimum_required(VERSION 3.16)

project(modernGUI VERSION 0.1 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(Qt6 6.4 REQUIRED COMPONENTS Quick)

qt_standard_project_setup()

qt_add_executable(appuntitled43
    main.cpp
)

qt_add_qml_module(appuntitled43
    URI untitled43
    VERSION 1.0
    QML_FILES
        Main.qml
)

# Qt for iOS sets MACOSX_BUNDLE_GUI_IDENTIFIER automatically since Qt 6.1.
# If you are developing for iOS or macOS you should consider setting an
# explicit, fixed bundle identifier manually though.
set_target_properties(appuntitled43 PROPERTIES
#    MACOSX_BUNDLE_GUI_IDENTIFIER com.example.appuntitled43
    MACOSX_BUNDLE_BUNDLE_VERSION ${PROJECT_VERSION}
    MACOSX_BUNDLE_SHORT_VERSION_STRING ${PROJECT_VERSION_MAJOR}.${PROJECT_VERSION_MINOR}
    MACOSX_BUNDLE TRUE
    WIN32_EXECUTABLE TRUE
)

target_link_libraries(appuntitled43
    PRIVATE Qt6::Quick
)

include(GNUInstallDirs)
install(TARGETS appuntitled43
    BUNDLE DESTINATION .
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
)
