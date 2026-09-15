#pragma once

#include <string>

using namespace std;

// apps/ 下各学习应用的根目录，只认环境变量 ATHENA_APPS_ROOT（ADR 0047）。
//
// 谁要让本程序能从学科图谱打开别的学科，谁就告诉它 apps/ 在哪——启动器在
// app.json 的 dev 声明里传。本程序不自己去找别人的目录：那既需要"当前可执行
// 文件在哪"这种没有跨平台 API 的能力，也越过了"应用之间不互相引用路径"
// 的边界（ADR 0032）。
//
// 拿不到就返回空串，调用方提示改用启动器，不抛出、不崩溃。
string external_apps_root();

// 本应用自己在仓库工作树里的根目录（`apps/cpp`），只认环境变量
// ATHENA_CPP_ROOT，由启动器在 app.json 的 dev 声明里传。
//
// 教学内容仍然一律从 GResource 读，这个路径只用来放**用户数据**：进度库要
// 随仓库走，换一台机器 clone 下来掌握度才还在（ADR 0053）。两者性质不同——
// 内容必须和二进制同版本，进度是使用者自己的东西。
//
// 发行包里没人传它，返回空串，调用方退回本机用户数据目录。
string own_app_root();
