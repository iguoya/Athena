---
chapter: chapter-basics
section: sec-basics-gobj-and-wrap
upstream-sha: 73444c2445e70d1201f9b8a5eecd111ff94c75023f59a5c68b0717f018277252
upstream-commit: b89295e22598db8697d1aa22dd528a103d956c9b
---

<!-- 来源：Programming with gtkmm 4 · Mixing C and C++ APIs
     分页严格跟随官方仓库结构（每节一页，对应官网 sec-sec-basics-gobj-and-wrap 页面）。
     引用块为英文原文，紧随段落为中文翻译；代码块照录不译。
     upstream-sha 变化即表示官方原文已改，本稿需要复核。 -->

> You can use C APIs which do not yet have convenient C++ interfaces. It is
> generally not a problem to use C APIs from C++, and gtkmm helps by providing
> access to the underlying C object, and providing an easy way to create a
> C++ wrapper object from a C object, provided that the C API is also based on
> the GObject system.

那些还没有顺手 C++ 接口的 C API 也可以用。在 C++ 里调用 C API 一般不成问题；
gtkmm 还帮了两把：让你能访问底层的 C 对象，并且在 C API 同样基于 GObject
系统的前提下，提供从 C 对象便捷创建 C++ 包装对象的途径。

> To use a gtkmm instance with a C function that requires a C GObject
> instance, use the C++ instance's gobj() function to obtain a pointer to the
> underlying C instance. For example:

要把 gtkmm 实例传给需要 C GObject 实例的 C 函数，用 C++ 实例的 gobj() 函数
拿到底层 C 实例的指针。例如：

```cpp
Gtk::Button button("example");
gtk_button_do_something_that_gtkmm_cannot(button.gobj());
```

> To obtain a gtkmm instance from a C GObject instance, use one of the many
> overloaded Glib::wrap() functions. The C instance's reference count is not
> incremented, unless you set the optional take_copy argument to true. For
> example:

反过来，要从 C GObject 实例得到 gtkmm 实例，用众多重载的 Glib::wrap() 函数
之一。除非把可选的 take_copy 参数设为 true，C 实例的引用计数不会增加。例如：

```cpp
GtkButton* cbutton = get_a_button();
Gtk::Button* button = Glib::wrap(cbutton);
button->set_label("Now I speak C++ too!");
```

> The C++ wrapper shall be explicitly deleted if

C++ 包装对象在满足以下条件时必须显式删除：

> - it's a widget or other class that inherits from Gtk::Object, and
> - the C instance has a floating reference when the wrapper is created, and
> - Gtk::manage() has not been called on it (which includes if it was created
>   with Gtk::make_managed()), or
> - Gtk::manage() was called on it, but it was never added to a parent.

- 它是控件或别的继承自 Gtk::Object 的类，且
- 创建包装对象时 C 实例带 floating reference（浮动引用），且
- 没有对它调用过 Gtk::manage()（包括用 Gtk::make_managed() 创建的情况），或者
- 调用过 Gtk::manage()，但从未把它加进任何父容器。

> Glib::wrap() binds the C and C++ instances to each other. Don't delete the
> C++ instance before you want the C instance to die.

Glib::wrap() 把 C 实例和 C++ 实例绑定在一起：不希望 C 实例死掉之前，别删
C++ 实例。

> In all other cases the C++ instance is automatically deleted when the last
> reference to the C instance is dropped. This includes all Glib::wrap()
> overloads that return a Glib::RefPtr.

在其他所有情况下，C 实例的最后一个引用被释放时，C++ 实例会自动删除——包括
所有返回 Glib::RefPtr 的 Glib::wrap() 重载。
