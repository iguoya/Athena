cmake_minimum_required(VERSION 3.5)

project(DesignEvolutionCpp LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_FLAGS " -Wno-error=deprecated-declarations -Wno-deprecated-declarations ")

find_package(PkgConfig REQUIRED)
find_package(Boost REQUIRED COMPONENTS)
if(Boost_FOUND)
    include_directories(${Boost_INCLUDE_DIR})
endif()
include_directories(/usr/include/gtk-4.0/)
pkg_check_modules(GTKMM REQUIRED gtkmm-4.0) # look into FindPkgConfig.cmake,

include_directories(${GTKMM_INCLUDE_DIRS})
#link_directories(${GTKMM_LIBRARY_DIRS})


include_directories (basic)

aux_source_directory (basic src_basic)

set(sources
        main.cpp
        ${src_basic}
)

add_executable(DesignEvolutionCpp ${sources} )
target_include_directories(DesignEvolutionCpp PRIVATE basic)
target_link_libraries(DesignEvolutionCpp ${GTKMM_LIBRARIES} ${Boost_LIBRARIES}  )

install(TARGETS DesignEvolutionCpp
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR} )
