import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2] / "tools"))
from quizlib import build, report, apply_new

INTRO, MARK, UTF8, PIT, HELP, EX = (
    "sec-internationalization-intro", "sec-i18n-marking-strings", "sec-i18n-expecting-utf8",
    "sec-i18n-pitfalls", "sec-i18n-getting-help-with-translations", "sec-i18n-example")

INPAGE = [
    dict(id="in27-intro-1", page=INTRO, pos=0,
         stem="i18n 和 l10n 这两个缩写，分别指什么工作？",
         right="i18n 让源码能被翻译，l10n 提供各语言的译文",
         wrong=["i18n 提供各语言的译文，l10n 让源码能被翻译",
                "i18n 指编译程序，l10n 指把程序安装到用户机器上",
                "二者是同一件事，只是 gettext 与 intltool 的叫法不同"],
         why="编写允许翻译的源码的过程叫国际化（internationalization，缩写 i18n）；本地化（localization，缩写 l10n）则基于这些源码提供其他语言的翻译文本。",
         ref="国际化与本地化：i18n 指让源码可翻译，l10n 指提供译文"),
    dict(id="in27-intro-3", page=INTRO, pos=1,
         stem="po 目录里的 LINGUAS 文件是下面这样，它要求 po 目录里还必须有什么？",
         code="""
# keep this file sorted alphabetically, one language code per line
de
ja""",
         right="de.po 和 ja.po，每个语言码都要有 .po",
         wrong=["de.mo 和 ja.mo：列出的语言码要有现成编译好的 .mo",
                "什么都不需要：LINGUAS 只是给翻译者看的备注",
                "de.pot 和 ja.pot：每种语言各有自己的 .pot 模板"],
         why="LINGUAS 是按字母排序的语言码列表（以 # 开头的行是注释），列出的每个语言码都必须有对应的 .po 文件。示例里就是 po 目录中的 de.po 与 ja.po，分别装着德语和日语译文。",
         ref="准备项目：LINGUAS 文件列出语言码，每个都需要对应的 .po"),
    dict(id="in27-mark-1", page=MARK, pos=2,
         stem="想用 Glib 提供的简短宏来标记这行里的字符串，需要先怎样、再怎样？",
         code="""
display_message(_("Getting ready for i18n."));""",
         right="先包含 <glibmm/i18n.h>，再用 _() 把字符串包起来",
         wrong=["先包含 <libintl.h>，再把宏名写成 GETTEXT()",
                "不需要包含头文件，_() 是 C++ 语言内建的运算符",
                "先包含 <glibmm/i18n.h>，再用 N_() 在运行时翻译"],
         why="字符串字面量按英文写在源码里，再用 gettext() 包起来。Glib 定义了更短的包装宏，只要 include <glibmm/i18n.h>，就可以把 display_message(\"...\") 换成 display_message(_(\"...\"))。",
         ref="标记字符串：include <glibmm/i18n.h>，用 _() 包装字符串字面量"),
    dict(id="in27-mark-2", page=MARK, pos=3,
         stem=".po 文件里有一条被标成 fuzzy，运行时会怎样？怎样让译文出现？",
         right="不会替换原文；去掉 fuzzy 标记后译文才会出现",
         wrong=["会优先替换原文，fuzzy 表示这条译文已经审定过",
                "会导致整个 .po 无法转换成 .mo，必须先去掉标记",
                "与普通条目没有区别，fuzzy 只影响 msgfmt 的警告"],
         why="fuzzy 标记的译文不会取代原始字符串；要让它们出现，只需去掉 fuzzy 标记。字符串内容变了而位置没变时，就会出现 fuzzy 标记。",
         ref="测试与添加翻译：fuzzy 标记的译文不会取代原文"),
    dict(id="in27-mark-3", page=MARK, pos=0,
         stem="用户的 locale 没有对应的 .mo 文件，程序执行到 _(\"Open\") 时会得到什么？",
         right="原始的英文字符串 \"Open\"",
         wrong=["空字符串，因为没有找到可用的译文",
                "抛出异常，程序必须捕获并改用默认语言",
                "最接近的其他语言的译文，由 gettext 自动挑选"],
         why="程序运行时，gettext 库在系统范围的目录里查找用户 locale 对应的 .mo 文件；执行到 gettext 调用时再找某个字符串的译文，如果找不到，就使用原始字符串。",
         ref="gettext 工作原理：找不到译文时使用原始字符串"),
    dict(id="in27-utf8-1", page=UTF8, pos=1,
         stem="当前 locale 不是 UTF-8 时，下面的写法可能让标签文字出错，原因是什么？",
         code="""
std::ostringstream output;
output << percentage << " % done";
label->set_text(output.str());""",
         right="经 std::string 隐式转成 ustring 时没有做区域编码转换",
         wrong=["ostringstream 不允许输出百分号，所以文字会残缺",
                "set_text() 只接受 char*，传入 std::string 会崩溃",
                "percentage 必须先用 _() 包起来，否则文字会乱码"],
         why="gtkmm 把 Glib::ustring 输出到 ostream 时会转成区域相关编码，反方向同理。但经过 std::string 再隐式转成 ustring 时这个机制失效；有非 ASCII 字符且 locale 不是 UTF-8，就得到损坏的 ustring。要手动转换：label->set_text(Glib::locale_to_utf8(output.str()))。",
         ref="期望 UTF-8：Glib::ustring 与 iostream，经 std::string 会出错，用 locale_to_utf8() 转换"),
    dict(id="in27-pit-1", page=PIT, pos=2,
         stem="下面这样拼接可翻译的片段，对翻译者有什么问题？应改成什么？",
         code="""
label.set_text(_("Really delete ") + filename + _(" now?"));""",
         right="片段无法按语法重排；改用 compose 与 %1",
         wrong=["没有问题：译者分别翻译前后缀，gettext 会自动重排它们",
                "必须改回 sprintf，因为 compose 不能出现在 _() 里",
                "filename 也要用 _() 包起来，否则 msgfmt 会报错"],
         why="用流或拼接组合文本时，每个文本片段单独翻译，译者无法按目标语言的语法重新排列它们。应避免这种情形，或改用 Glib::ustring::compose(_(\"Really delete %1 now?\"), filename)，整句交给译者。",
         ref="易错点：字符串组合，每个片段单独翻译，改用 Glib::ustring::compose()"),
    dict(id="in27-pit-2", page=PIT, pos=3,
         stem="下面的 C_() 比起普通的 _() 多解决了什么问题？",
         code="""
Glib::ustring text(C_("noun", "jumps"));""",
         right="用上下文区分英文相同、含义不同的词条",
         wrong=["给译文自动加上 [noun] 之类的标签，运行时无需剥掉",
                "让该字符串绕过 gettext，直接作为译文显示",
                "只为同一个字符串生成一份译文，供所有语境共享"],
         why="英文字符串是查找译文的键；两个相同的英文词含义不同时，译文可能不同，会产生冲突。原文的办法是写成 \"jumps[noun]\" 之类再在 gettext 之外剥掉，而用 Glib 的宏更简单：用 C_() 代替 _()。",
         ref="易错点：相同字符串、不同语义，用 C_() 代替 _()"),
    dict(id="in27-ex-1", page=EX, pos=0,
         stem="示例 main() 里的这三行，应当放在哪里？",
         code="""
bindtextdomain(GETTEXT_PACKAGE, PROGRAMNAME_LOCALEDIR);
bind_textdomain_codeset(GETTEXT_PACKAGE, "UTF-8");
textdomain(GETTEXT_PACKAGE);""",
         right="main() 靠前，创建 Application 之前",
         wrong=["窗口构造函数里，在 set_title() 之后调用",
                "main() 末尾，在 run 返回之后再调用",
                "只放在配置文件里，源码中不需要出现"],
         why="文档让你把初始化 gettext 的代码加在 main.cc 的开头。示例 main() 先按配置文件设置 locale，再调用这三行，之后才用 Gtk::Application::create() 创建应用。",
         ref="示例：main() 开头初始化 gettext，随后才创建 Application"),
    dict(id="in27-help-1", page=HELP, pos=1,
         stem="自由软件想请 GNOME 翻译项目帮忙，文档给出的第一步是什么？",
         right="源码放进可访问的 git，向 damned-lies 提 issue",
         wrong=["只把编译好的安装包发给翻译小组，不用公开源码",
                "自己翻译 .pot 文件，再请翻译项目审核并发布",
                "在发版当天提交所有字符串，翻译随后自动合入"],
         why="工作方式是：把源码上传到译者能访问的 git 仓库，然后向 damned-lies 项目提 issue，请求把程序加入待翻译模块列表；还要更新 po/POTFILES.in，并在发版前至少几天冻结字符串。",
         ref="获得翻译帮助：GNOME 翻译项目，git 仓库加 damned-lies issue"),
]

CHECKPOINT = [
    dict(id="in27-cp-1", pos=2, locator="官方节页 sec-i18n-marking-strings",
         stem="从提取字符串到程序运行，翻译文件的格式依次是怎样变化的？",
         right=".pot 模板，复制出 .po，安装时转成 .mo",
         wrong=[".mo 模板，译者复制出 .po，安装时合并成 .pot",
                "只有 .po 一种文件，运行时 gettext 直接读取它",
                ".po 模板，译者复制出 .pot，运行时转成 .mo"],
         why="xgettext 或 intltool-update 提取字符串，生成 mypackage.pot；译者把它复制为 localename.po 并翻译；安装时 .po 被转成二进制 .mo，放进系统的 locale 目录；运行时 gettext 按用户 locale 查找 .mo。",
         ref="综合 gettext 工作原理：.pot → .po → .mo"),
    dict(id="in27-cp-2", pos=3, locator="官方节页 sec-i18n-pitfalls",
         stem="设计界面时，对翻译后字符串占用的屏幕空间，文档的建议是什么？",
         right="无法预知，可能是英文的两倍；大多数部件运行时会自动扩展",
         wrong=["德语等欧洲语言比英文短，所以按英文宽度固定即可",
                "必须为每种语言单独手写一个固定尺寸的界面",
                "翻译者负责把译文缩写到与英文等长，界面无需考虑"],
         why="你永远不知道翻译后的字符串会占多大空间，很可能是英文原文的两倍；好在大多数 gtkmm 部件会在运行时扩展到所需大小，所以不要把标签的宽度写死。",
         ref="综合易错点：翻译后字符串的显示大小无法预知"),
]

KP = dict(id="gtkmm.i18n.quizset", title="国际化测验集", difficulty=3, mastery_goal="required")

if __name__ == "__main__":
    inpage = [build(s) for s in INPAGE]
    cp = [build(s) for s in CHECKPOINT]
    report(inpage + cp)
    if "--apply" in sys.argv:
        apply_new("chapter-internationalization", KP, inpage, cp)
        print("written")
