---
chapter: chapter-basics
section: sec-headers-and-linking
upstream-sha: 08309118237ca1c14b39fd925cc46200ccc8834f841995ca77d04a6625613ec0
upstream-commit: b89295e22598db8697d1aa22dd528a103d956c9b
---

<!-- 来源：Programming with gtkmm 4 · Headers and Linking
     分页严格跟随官方仓库结构（每节一页，对应官网 sec-sec-headers-and-linking 页面）。
     引用块为英文原文，紧随段落为中文翻译；代码块照录不译。
     upstream-sha 变化即表示官方原文已改，本稿需要复核。 -->

> Although we have shown the compilation command for the simple example, you
> really should use the Meson build system. The examples used in this book
> are included in the gtkmm-documentation package, with appropriate build
> files, so we won't show the build commands in future. The README file in
> gtkmm-documentation describes how to build the examples.

虽然上面给出了简单示例的编译命令，但实际开发应该使用 Meson 构建系统。本书的
示例都收录在 gtkmm-documentation 包里，并带有相应的构建文件，所以之后不再
罗列构建命令。gtkmm-documentation 的 README 文件描述了如何构建这些示例。

> To simplify compilation, we use pkg-config, which is present in all
> (properly installed) gtkmm installations. This program 'knows' what
> compiler switches are needed to compile programs that use gtkmm. The
> --cflags option causes pkg-config to output a list of include directories
> for the compiler to look in; the --libs option requests the list of
> libraries for the compiler to link with and the directories to find them
> in. Try running it from your shell-prompt to see the results on your
> system.

为了简化编译，我们使用 pkg-config——一切（正确安装的）gtkmm 环境里都有它。
这个程序「知道」编译使用 gtkmm 的程序需要哪些编译开关。--cflags 让
pkg-config 输出编译器的头文件搜索目录列表；--libs 请求链接库列表及其所在
目录。可以在 shell 里亲手跑一下，看看你系统上的输出。

> However, this is even simpler when using the dependency() function in a
> meson.build file with Meson. For instance:

而用 Meson 时，在 meson.build 文件里调用 dependency() 函数还要更简单。例如：

```meson
gtkmm_dep = dependency('gtkmm-4.0', version: '>= 4.6.0')
```

> This checks for the presence of gtkmm and defines gtkmm_dep for use in your
> meson.build files. For instance:

这一句会检查 gtkmm 是否可用，并定义出 gtkmm_dep 供 meson.build 使用。例如：

```meson
exe_file = executable('my_program', 'my_source1.cc', 'my_source2.cc',
  dependencies: gtkmm_dep,
  win_subsystem: 'windows',
)
```

> gtkmm-4.0 is the name of the current stable API. There are older APIs
> called gtkmm-2.4 and gtkmm-3.0 which install in parallel when they are
> available. There are several versions of gtkmm-2.4, such as gtkmm 2.10 and
> there are several versions of the gtkmm-3.0 API. Note that the API name does
> not change for every version because that would be an incompatible API and
> ABI break. There might be a future gtkmm-5.0 API which would install in
> parallel with gtkmm-4.0 without affecting existing applications.

gtkmm-4.0 是当前稳定 API 的名字。还有更老的 API 叫 gtkmm-2.4 和 gtkmm-3.0，
如果系统里有的话，它们与 gtkmm-4.0 并行安装。gtkmm-2.4 有多个版本（比如
gtkmm 2.10），gtkmm-3.0 API 也有多个版本。注意：API 名字不会随每个版本改变，
因为改名就意味着不兼容的 API/ABI 断裂。将来可能出现 gtkmm-5.0 API，它将与
gtkmm-4.0 并行安装，不影响现有应用。

> If you start by experimenting with a small application that you plan to use
> just for yourself, it's easier to start with a meson.build similar to the
> meson.build files in the Building applications chapter.

如果你想先做一个自用的小应用练手，直接参考「Building applications」一章里的
meson.build 文件来起步会更容易。

> If you use the older Autotools build system, see also the GNU site. It has
> more information about autoconf and automake. There are also some books
> describing Autotools: "GNU Autoconf, Automake, and Libtool" by Gary Vaughan
> et al. and "Autotools, A Practitioner's Guide to GNU Autoconf, Automake,
> and Libtool" by John Calcote.

如果你用的是更老的 Autotools 构建系统，另请参阅 GNU 网站，那里有关于
autoconf 和 automake 的更多信息。也有几本书专门讲 Autotools：Gary Vaughan 等
人的《GNU Autoconf, Automake, and Libtool》，以及 John Calcote 的
《Autotools, A Practitioner's Guide to GNU Autoconf, Automake, and Libtool》。
