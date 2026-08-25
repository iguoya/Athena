#pragma once

#include <gtkmm.h>

#include <vector>

using namespace std;

// 全应用共用的对话框外观和生命周期管理，让“设置”“运行历史”“AI 自测”
// “关于”这些独立弹出的对话框长得像同一个应用的一部分——原生标题栏 +
// 左对齐的表单式内容 + 底部居中一行操作按钮，不是每个对话框各画各的。
// 从 ui/learning_dialogs.cc 提出来，因为“关于”这类跟学习流程无关的
// 对话框（在 mainwindow.cc 里）也要用同一套外观，不属于 LearningDialogs
// 这个业务类的职责范围。

// 在对话框内容区底部居中放一行按钮；不加“关闭”——系统对话框本身自带
// 原生标题栏关闭按钮，不需要重复一个。extra_buttons 为空时什么都不做，
// 调用方自己决定按钮颜色（加 css class）和点击行为。
void append_dialog_action_bar(
    Gtk::Box* content_box, const vector<Gtk::Button*>& extra_buttons);

// 打开模态对话框前调用。传入的 dialog 必须是 `new` 出来的普通指针，
// 不能用 Gtk::make_managed 创建——GTK4 里 GtkWindow 的 hide-on-close
// 默认是 false，点原生标题栏关闭按钮会直接销毁窗口而不是隐藏它；如果
// 对话框是 make_managed 出来的，gtkmm 会在底层对象销毁的同时同步
// delete 这份 C++ 包装。有异步回调（网络请求）期间还持有对话框指针的
// 场景，用户提前关闭对话框会让回调踩中已经被 delete 掉的悬空指针，是
// 真实的 use-after-free，不是理论风险。
//
// 这里反过来强制 set_hide_on_close(true)：点关闭按钮总是隐藏、不销毁；
// 对话框改由这里在隐藏之后显式 delete——排到事件循环下一轮再删，不在
// hide 信号处理函数内部直接删自己（那个调用栈本身还压在这个对象上，
// 是未定义行为）；调用方自己的 signal_hide 清理逻辑（如翻转
// dialog_alive、reset article_view）要在 lock_for_modal_dialog 之前
// 连接，才能保证在这里删除之前先跑到——GTK 信号按连接顺序调用。
//
// 同时禁用主窗口自身的输入，隐藏时恢复：观察到过等待期间（网络请求慢
// 的话有好几秒到十几秒窗口期）用户点回主窗口、主窗口被系统前置盖住
// 对话框的情况——GTK4 的 set_modal(true) 在这里没能防住。禁用主窗口
// 输入是应用层能做的、不依赖窗口管理器行为的兜底：即便主窗口的原生
// 窗口被前置到对话框之上，用户也点不动里面任何控件。present() 保证
// 首次显示就被前置和聚焦，而不只是 show()。
//
// 内容完全静态、没有任何异步操作的对话框（比如“关于”）可以不经过这条
// 路径，惰性创建一次长期复用即可——见 MainWindow::show_about_dialog()。
void lock_for_modal_dialog(Gtk::Window& main_window, Gtk::Dialog& dialog);
