---
chapter: chapter-introduction
section: sec-gtkmm
upstream-sha: 737d974b370b5bc7ff6a8717e36e5032464f565cb4d04b8c66d9a21beffdcd68
upstream-commit: b89295e22598db8697d1aa22dd528a103d956c9b
---

<!-- 来源：Programming with gtkmm 4 · gtkmm
     分页严格跟随官方仓库结构（每节一页，对应官网 sec-sec-gtkmm 页面）。
     引用块为英文原文，紧随段落为中文翻译；代码块照录不译。
     upstream-sha 变化即表示官方原文已改，本稿需要复核。 -->

> gtkmm is a C++ wrapper for GTK, a library used to create graphical user
> interfaces. It is licensed using the LGPL license, so you can develop open
> software, free software, or even commercial non-free software using gtkmm
> without purchasing licenses.

gtkmm 是 GTK 的 C++ 包装；GTK 是一个用来创建图形用户界面的库。gtkmm 采用
LGPL 许可，因此无论开发开源软件、自由软件，还是商业非自由软件，使用 gtkmm
都无需购买授权。

> gtkmm was originally named gtk-- because GTK was originally named GTK+ and
> had a + in the name. However, as -- is not easily indexed by search
> engines, the package generally went by the name gtkmm, and that's what we
> stuck with.

gtkmm 最初叫 gtk--：因为 GTK 最初叫 GTK+，名字里带一个 `+`。不过 `--` 不利于
搜索引擎收录，这个包渐渐就以 gtkmm 之名为人所知，这个名字也就沿用了下来。

### Why use gtkmm instead of GTK?（为什么用 gtkmm 而不是 GTK？）

> gtkmm allows you to write code using normal C++ techniques such as
> encapsulation, derivation, and polymorphism. As a C++ programmer you
> probably already realize that this leads to clearer and better organized
> code.

gtkmm 让你用普通的 C++ 技术写代码——封装、派生、多态。作为 C++ 程序员你大概
已经明白，这会让代码更清晰、组织得更好。

> gtkmm is more type-safe, so the compiler can detect errors that would only
> be detected at run time when using C. This use of specific types also makes
> the API clearer because you can see what types should be used just by
> looking at a method's declaration.

gtkmm 的类型安全更强，许多在 C 里要到运行时才暴露的错误，编译器就能查出来。
具体类型也让 API 更清楚：光看方法的声明，就知道该用什么类型。

> Inheritance can be used to derive new widgets. The derivation of new
> widgets in GTK C code is so complicated and error prone that almost no C
> coders do it. As a C++ developer you know that derivation is an essential
> Object Orientated technique.

可以用继承来派生新控件。在 GTK 的 C 代码里派生新控件复杂且容易出错，几乎没有
C 程序员这么做；而作为 C++ 开发者你知道，派生是面向对象的基本技术。

> Member instances can be used, simplifying memory management. All GTK C
> widgets are dealt with by use of pointers. As a C++ coder you know that
> pointers should be avoided where possible.

可以用成员实例，从而简化内存管理。GTK 的 C 控件全靠指针操作；作为 C++ 程序员
你知道，指针应能免则免。

> gtkmm involves less code compared to GTK, which uses prefixed function
> names and lots of cast macros.

与 GTK 相比，gtkmm 的代码量更少——GTK 依靠带前缀的函数名和大量强制转换宏。

### gtkmm compared to Qt（gtkmm 与 Qt 的比较）

> Trolltech's Qt is the closest competition to gtkmm, so it deserves
> discussion.

Trolltech 的 Qt 是与 gtkmm 最接近的竞争者，值得拿来讨论。

> gtkmm developers tend to prefer gtkmm to Qt because gtkmm does things in a
> more C++ way. Qt originates from a time when C++ and the standard library
> were not standardized or well supported by compilers. It therefore
> duplicates a lot of stuff that is now in the standard library, such as
> containers and type information. Most significantly, Trolltech modified the
> C++ language to provide signals, so that Qt classes cannot be used easily
> with non-Qt classes. gtkmm was able to use standard C++ to provide signals
> without changing the C++ language. See the FAQ for more detailed
> differences.

gtkmm 的开发者们更偏爱 gtkmm，因为它做事的方式更「C++」。Qt 诞生于 C++ 和
标准库尚未标准化、编译器支持也不完善的年代，于是重复造了大量如今标准库里已经
有的东西，比如容器和类型信息。最关键的是，Trolltech 修改了 C++ 语言本身来提供
信号机制，导致 Qt 类很难与非 Qt 类混用。gtkmm 则用标准 C++ 实现了信号，无需
改动语言。更详细的差异对比见 FAQ。

### gtkmm is a wrapper（gtkmm 是一个包装）

> gtkmm is not a native C++ toolkit, but a C++ wrapper of a C toolkit. This
> separation of interface and implementation has advantages. The gtkmm
> developers spend most of their time talking about how gtkmm can present the
> clearest API, without awkward compromises due to obscure technical details.
> We contribute a little to the underlying GTK code base, but so do the C
> coders, and the Perl coders and the Python coders, etc. Therefore GTK
> benefits from a broader user base than language-specific toolkits - there
> are more implementers, more developers, more testers, and more users.

gtkmm 不是原生 C++ 工具集，而是 C 工具集的 C++ 包装。接口与实现的分离自有其
好处：gtkmm 的开发者可以把大部分精力花在「如何呈现最清晰的 API」上，不必为
晦涩的技术细节做出难看的妥协。我们对底层 GTK 代码库也有些贡献，但 C 程序员、
Perl 程序员、Python 程序员等同样在贡献。因此，相比特定语言的工具集，GTK 受益
于更广泛的用户群——实现者更多、开发者更多、测试者更多、用户也更多。
