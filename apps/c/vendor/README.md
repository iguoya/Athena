# vendor

第三方源码放这里，随仓库 vendor 一份，不用 submodule。

## LVGL

窗口后端需要 LVGL，放成 `vendor/lvgl/`，即该目录下直接能看到 `lvgl.h`
和它自己的 `CMakeLists.txt`：

```sh
curl -L -o /tmp/lvgl.tar.gz \
  https://github.com/lvgl/lvgl/archive/refs/tags/v9.2.2.tar.gz
tar -xzf /tmp/lvgl.tar.gz -C /tmp
mv /tmp/lvgl-9.2.2 apps/c/vendor/lvgl
```

还需要 SDL2（LVGL 在桌面上靠它开窗口）：`brew install sdl2`，
Ubuntu 上是 `apt install libsdl2-dev`。

两者都就位后重新 configure，CMake 会自动从占位实现切到真窗口：

```sh
cmake -S apps/c -B apps/c/build
cmake --build apps/c/build
```

`vendor/lvgl/` 在 `.gitignore` 里——它是外部源码，不进本仓库的历史。
