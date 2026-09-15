#include "ui/athena.h"

#include <gtksourceview/gtksource.h>

#include <glibmm/miscutils.h>

int main(int argc, char* argv[]) {
  // 只锁定消息翻译用的语言，不动别的 locale 分类——GTK 自带的系统级控件（如
  // 文件选择对话框、颜色选择器上的按钮）的文本走 gettext；不依赖外部 shell
  // 或系统会话是否正确设置了 LANG（终端启动时经常是 "C"，即便系统偏好设置
  // 是中文），主动锁定成中文，保证跟 Athena 自己手写的中文控件文本一致。
  //
  // 用 LANGUAGE 环境变量而不是 setlocale(LC_MESSAGES, ...)：LC_MESSAGES 是
  // POSIX 扩展，MSVC / UCRT 的 <clocale> 里根本没有这个宏，Windows 上直接
  // 编不过（ADR 0047）。gettext 的查找顺序里 LANGUAGE 优先级最高，三个平台
  // 上语义一致，而且不要求系统装了 zh_CN.UTF-8 这个 locale。
  Glib::setenv("LANGUAGE", "zh_CN", true);
  // GNOME 顶栏 / Dash / Alt-Tab 显示的应用名：不设置时会退回应用 ID
  // （cn.yatiger.athena）的末段，在 Ubuntu 上显示成小写 "athena"。
  Glib::set_application_name("计算机与电子信息学习实验室");
  gtk_source_init();
  int status = 0;
  {
    auto app = Athena::create();
    status = app->run(argc, argv);
  }
  gtk_source_finalize();
  return status;
}
