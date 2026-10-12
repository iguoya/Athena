# example.buttons.button — 官方示例的学习者副本

来自 `exercise/buttons/button`（官方 `examples/book/` 的逐字镜像，版本随
`upstream.json` 钉点）；`CMakeLists.txt` 与 `.vscode/` 由课程壳生成。
这里是学习者的地盘，随便改；想回到官方原样，删掉整个目录后在课程里
重新点「打开工作区」。

## 构建与运行

命令行（Windows 在 MSYS2 MINGW64 Shell 里；macOS/Linux 直接用）：

```sh
cmake -G Ninja -S . -B build
cmake --build build
./build/example-buttons-button
```

VS Code：`Ctrl+Shift+B` 构建默认任务；任务「run」构建并运行（窗口从
本目录启动——button 示例从工作目录读 `info.xpm`）。F5 调试有两个配置：
「调试（C/C++ 扩展）」需要 ms-vscode.cpptools，「调试（CodeLLDB 扩展）」
需要 vadimcn.vscode-lldb，装了哪个用哪个。
