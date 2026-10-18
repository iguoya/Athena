// T-105 第 16 章代码题断言验证（不进构建，仅一次性别证据）：
//   A. 程序性 set_value() 也会发出 value_changed，处理函数里 get_value() 已是新值
//   B. 两个 Scale 共享同一 Adjustment：一个 set_value()，另一个 get_value() 同步
//   C. set_value() 传超出 [lower, upper] 的值会被钳到边界（观察项，不用于题目）
#include <gtkmm.h>
#include <iostream>

int main()
{
  auto app = Gtk::Application::create("org.athena.verify.adj16");

  // A
  auto adj = Gtk::Adjustment::create(0.0, 0.0, 101.0, 1.0, 5.0, 0.0);
  int fired = 0;
  double seen = -1.0;
  adj->signal_value_changed().connect([&] {
    ++fired;
    seen = adj->get_value();
  });
  adj->set_value(42.0);
  std::cout << "A: fired=" << fired << " seen=" << seen << std::endl;

  // B
  auto adj2 = Gtk::Adjustment::create(0.0, 0.0, 100.0, 1.0, 10.0, 0.0);
  Gtk::Scale scale1(adj2, Gtk::Orientation::HORIZONTAL);
  Gtk::Scale scale2(adj2, Gtk::Orientation::HORIZONTAL);
  scale1.set_value(80.0);
  std::cout << "B: scale2.get_value()=" << scale2.get_value() << std::endl;

  // C
  adj2->set_value(500.0);
  std::cout << "C: after set_value(500) get_value()=" << adj2->get_value() << std::endl;
  adj2->set_value(-50.0);
  std::cout << "C: after set_value(-50) get_value()=" << adj2->get_value() << std::endl;
  return 0;
}
