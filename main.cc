#include "athena.h"

#include <gtksourceview/gtksource.h>

#include <clocale>

int main(int argc, char* argv[]) {
  // 只锁定消息翻译用的 locale，不动 LC_ALL——GTK 自带的系统级控件（如
  // 文件选择对话框、颜色选择器上的按钮）的文本走 gettext，依赖运行时
  // LC_MESSAGES 环境变量决定用哪种语言；不依赖外部 shell/系统会话是否
  // 正确设置了 LANG（终端启动时经常是 "C"，即便系统偏好设置是中文），
  // 主动锁定成中文，保证跟 Athena 自己手写的中文控件文本一致。系统没有
  // 安装 zh_CN.UTF-8 这个 locale 时 setlocale 静默失败、不影响其他行为，
  // 只是这类控件的内置文本会退回英文。
  setlocale(LC_MESSAGES, "zh_CN.UTF-8");
  gtk_source_init();
  int status = 0;
  {
    auto app = Athena::create();
    status = app->run(argc, argv);
  }
  gtk_source_finalize();
  return status;
}
