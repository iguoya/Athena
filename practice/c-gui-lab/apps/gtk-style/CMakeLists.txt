find_package(PkgConfig REQUIRED)
pkg_check_modules(GTK4 REQUIRED gtk4)
pkg_check_modules(ADW REQUIRED libadwaita-1)

add_executable(gtk-style gtk-style.c)

target_include_directories(gtk-style PRIVATE ${GTK4_INCLUDE_DIRS} ${ADW_INCLUDE_DIRS})
target_link_directories(gtk-style PRIVATE ${GTK4_LIBRARY_DIRS} ${ADW_LIBRARY_DIRS})
target_link_libraries(gtk-style PRIVATE ${GTK4_LIBRARIES} ${ADW_LIBRARIES})
target_compile_options(gtk-style PRIVATE ${GTK4_CFLAGS_OTHER} ${ADW_CFLAGS_OTHER})

# style.css 复制到 exe 同目录，程序运行时加载
add_custom_command(TARGET gtk-style POST_BUILD
  COMMAND ${CMAKE_COMMAND} -E copy_if_different
          ${CMAKE_CURRENT_SOURCE_DIR}/style.css $<TARGET_FILE_DIR:gtk-style>/style.css)
