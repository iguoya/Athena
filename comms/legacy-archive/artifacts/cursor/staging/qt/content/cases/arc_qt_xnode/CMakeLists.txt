cmake_minimum_required(VERSION 3.5)

project(XNode LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)




set(PROJECT_SOURCES
    main.cpp
    xnode.h xnode.cpp
    server.h server.cpp
    client.h client.cpp
    config.json
)

add_executable(XNode
    ${PROJECT_SOURCES}
)

file(COPY ${CMAKE_CURRENT_SOURCE_DIR}/config.json
     DESTINATION ${CMAKE_CURRENT_BINARY_DIR})

configure_file(${CMAKE_CURRENT_SOURCE_DIR}/config.json
    ${CMAKE_CURRENT_BINARY_DIR} COPYONLY)

#add_executable(XNode main.cpp xnode.h xnode.cpp)


add_subdirectory(Application)
add_subdirectory(NodeLibrary)
add_subdirectory(NodeClient)
add_subdirectory(NodeServer)
add_subdirectory(StandAloneNode)
add_subdirectory(Server)
add_subdirectory(Client)
