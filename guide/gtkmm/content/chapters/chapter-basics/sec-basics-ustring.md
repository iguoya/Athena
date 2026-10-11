---
chapter: chapter-basics
section: sec-basics-ustring
upstream-sha: 7e33215c5028eeb75e2c89df995dd400a0cdc6ca68f3681405dae151be09059e
upstream-commit: b89295e22598db8697d1aa22dd528a103d956c9b
---

<!-- 来源：Programming with gtkmm 4 · Glib::ustring
     分页严格跟随官方仓库结构（每节一页，对应官网 sec-sec-basics-ustring 页面）。
     引用块为英文原文，紧随段落为中文翻译；代码块照录不译。
     upstream-sha 变化即表示官方原文已改，本稿需要复核。 -->

> You might be surprised to learn that gtkmm doesn't use std::string in its
> interfaces. Instead it uses Glib::ustring, which is so similar and
> unobtrusive that you could actually pretend that each Glib::ustring is a
> std::string and ignore the rest of this section. But read on if you want to
> use languages other than English in your application.

你可能会惊讶：gtkmm 的接口里用的不是 std::string，而是 Glib::ustring。它与
std::string 相似到几乎不引人注意的程度——你完全可以假装每个 Glib::ustring
就是 std::string，然后跳过本节剩下的部分。但如果你的应用要用英语以外的语言，
请往下读。

> std::string uses 8 bits per character, but 8 bits aren't enough to encode
> languages such as Arabic, Chinese, and Japanese. Although the encodings for
> these languages have been specified by the Unicode Consortium, the C and
> C++ languages do not yet provide any standardized Unicode support for UTF-8
> encoding. GTK and GNOME chose to implement Unicode using UTF-8, and that's
> what is wrapped by Glib::ustring. It provides almost exactly the same
> interface as std::string, along with automatic conversions to and from
> std::string.

std::string 每个字符 8 个比特，而 8 个比特不足以编码阿拉伯文、中文、日文这些
语言。这些语言的编码虽已由 Unicode 联盟制定，但 C 和 C++ 语言至今没有为 UTF-8
编码提供标准化的 Unicode 支持。GTK 和 GNOME 选择用 UTF-8 实现 Unicode，
Glib::ustring 包装的正是它。它提供的接口与 std::string 几乎完全一致，并带有
与 std::string 的双向自动转换。

> One of the benefits of UTF-8 is that you don't need to use it unless you
> want to, so you don't need to retrofit all of your code at once.
> std::string will still work for 7-bit ASCII strings. But when you try to
> localize your application for languages like Chinese, for instance, you
> will start to see strange errors, and possible crashes. Then all you need
> to do is start using Glib::ustring instead.

UTF-8 的一个好处是：不用它可以不用，不必一次性改造全部代码。对 7 位 ASCII
字符串，std::string 依然可用。但当你开始把应用本地化成中文之类的语言时，就会
开始见到奇怪的错误，甚至崩溃。到那时，改用 Glib::ustring 就好。

> Note that UTF-8 isn't compatible with 8-bit encodings like ISO-8859-1. For
> instance, German umlauts are not in the ASCII range and need more than 1
> byte in the UTF-8 encoding. If your code contains 8-bit string literals, you
> have to convert them to UTF-8 (e.g. the Bavarian greeting "Grüß Gott" would
> be "Gr\xC3\xBC\xC3\x9F Gott").

注意：UTF-8 与 ISO-8859-1 这类 8 位编码不兼容。比如德语的变音符不在 ASCII
范围内，UTF-8 编码下需要不止 1 个字节。如果代码里有 8 位字符串字面量，必须
转换成 UTF-8（例如巴伐利亚问候语「Grüß Gott」要写成
"Gr\xC3\xBC\xC3\x9F Gott"）。

> You should avoid C-style pointer arithmetic, and functions such as
> strlen(). In UTF-8, each character might need anywhere from 1 to 6 bytes, so
> it's not possible to assume that the next byte is another character.
> Glib::ustring worries about the details of this for you so you can use
> methods such as Glib::ustring::substr() while still thinking in terms of
> characters instead of bytes.

应当避免 C 风格的指针运算，以及 strlen() 之类的函数。UTF-8 中一个字符可能占
1 到 6 个字节，不能假定下一个字节就是下一个字符。Glib::ustring 替你操心这些
细节：你可以继续用 Glib::ustring::substr() 之类的方法，按字符而不是按字节
思考。

> Unlike the Windows UCS-2 Unicode solution, this does not require any
> special compiler options to process string literals, and it does not result
> in Unicode executables and libraries which are incompatible with ASCII
> ones.

与 Windows 的 UCS-2 Unicode 方案不同，这套做法处理字符串字面量不需要任何特殊
编译选项，也不会产生与 ASCII 版本互不兼容的 Unicode 可执行文件和库。

> Reference

（参考文档链接见原页面末尾。）
