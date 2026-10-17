import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2] / "tools"))
from quizlib import build, report

INTRO, MARK, UTF8, PIT, HELP, EX = (
    "sec-internationalization-intro",
    "sec-i18n-marking-strings",
    "sec-i18n-expecting-utf8",
    "sec-i18n-pitfalls",
    "sec-i18n-getting-help-with-translations",
    "sec-i18n-example",
)

INPAGE = [
    dict(id="in27-intro-1", page=INTRO, pos=1,
         stem="原文说：若项目用 meson（推荐）做本地化，本章 autotools/intltool 小节该怎么处理？",
         right="去看 Meson 手册 Localisation，然后可跳过本节",
         wrong=["仍须完整抄一遍 configure.ac 里的 IT_PROG_INTLTOOL",
                "meson 不能做 i18n，必须改回 autotools 才能翻译",
                "只需建 po/ 目录，Meson 会忽略 gettext 相关文件"],
         why="原文 note：If you are using meson (recommended), see Meson's Localisation chapter. You can then skip this section。intltool/autotools 说明面向旧流程；meson 用户不必硬跟。",
         ref="Preparing your project：meson 用户可跳过 intltool 小节"),
    dict(id="in27-mark-1", page=MARK, pos=2,
         stem="要把可译字符串改成 Glib 短宏写法，需要先怎样、再怎样？",
         code="""
display_message(_("Getting ready for i18n."));""",
         right="先 #include <glibmm/i18n.h>，再用 _()",
         wrong=["先 #include <libintl.h>，宏名必须写成 GETTEXT()",
                "不必 include，_() 是语言内建，编译器直接替换",
                "用 N_() 包运行时字符串，_() 只给注释翻译员看"],
         why="原文：Glib 提供较短的 gettext 支持宏；要使用它们就 include <glibmm/i18n.h>，再把 display_message(\"...\") 换成 display_message(_(\"...\"))。",
         ref="Marking strings：glibmm/i18n.h 与 _()"),
    dict(id="in27-mark-2", page=MARK, pos=3,
         stem=".po 里某条带 fuzzy 标记时，运行时会怎样？怎样才会用上译文？",
         right="模糊译文不会替换原文；去掉 fuzzy 才生效",
         wrong=["fuzzy 表示已审定，运行时优先用这条译文",
                "带 fuzzy 的条目会让整个 .mo 安装失败",
                "fuzzy 只影响 msgfmt 警告，运行行为与普通条目相同"],
         why="原文：.po 里标为 fuzzy 的翻译不会取代原始字符串；要让它们出现，去掉 fuzzy 标记。字符串内容变了但位置仍相同时会出现 fuzzy。",
         ref="Testing and adding translations：fuzzy 标记"),
    dict(id="in27-utf8-1", page=UTF8, pos=0,
         stem="下面写法在非 UTF-8 区域设置下，为何可能弄坏标签文字？",
         code="""
std::ostringstream output;
output << percentage << " % done";
label->set_text(output.str());  // 隐式转成 Glib::ustring""",
         right="经 std::string 中转时，非 ASCII 可能已是错编码",
         wrong=["ostringstream 禁止写入百分号，编译阶段就会失败",
                "set_text 只接受 char*，传 string 会直接崩溃",
                "percentage 必须先 _(")，否则 gettext 拒绝绑定域"],
         why="原文：与 iostream 互转会做区域编码转换；若先写入 std::string 再隐式转 ustring，非 ASCII 且当前 locale 非 UTF-8 时会损坏。应用 Glib::locale_to_utf8(output.str())。日常文本用 Glib::ustring，勿依赖 strlen()/按字节假设。",
         ref="Expecting UTF8：iostream 经 std::string 中转的陷阱"),
    dict(id="in27-pit-1", page=PIT, pos=2,
         stem="下面这种拼接对翻译有什么问题？应改成什么？",
         code="""
label.set_text(_("Really delete ") + filename + _(" now?"));""",
         right="片段无法重排；改用 ustring::compose 与 %1",
         wrong=["完全没问题：译者会分别译前缀和后缀再拼回",
                "必须改回 sprintf，compose 不能出现在 _() 里",
                "filename 也要用 _() 包一层，否则 msgfmt 报错"],
         why="原文：流式/拼接把文本拆成碎片，译者无法按目标语语法重排。应避免，或用 Glib::ustring::compose(_(\"Really delete %1 now?\")，filename)。同义异境用 C_()；源码里不能写非 ASCII（如 ©）。",
         ref="Pitfalls：Composition of strings；兼及 C_() 与非 ASCII"),
    dict(id="in27-help-1", page=HELP, pos=1,
         stem="自由软件想借 GNOME 翻译项目帮忙，第一步关键是？",
         right="源码放可访问的 git，并向 damned-lies 提 issue",
         wrong=["只发二进制安装包给译者，不必公开任何源码仓库",
                "在未开放的私有仓库关 issue，干等官方来爬取仓库",
                "先把程序改成专有许可，翻译项目才接受付费订单"],
         why="原文：程序须是 free software；把源码放到译者能访问的 git，再向 damned-lies 提 issue 请求加入待译模块列表。还要维护 po/POTFILES.in，发版前冻结字符串。",
         ref="Getting help with translations：Translation Project / damned-lies"),
    dict(id="in27-ex-1", page=EX, pos=3,
         stem="示例 main 在创建 Application 之前，用哪三步初始化 gettext？",
         code="""
bindtextdomain(GETTEXT_PACKAGE, PROGRAMNAME_LOCALEDIR);
bind_textdomain_codeset(GETTEXT_PACKAGE, "UTF-8");
textdomain(GETTEXT_PACKAGE);""",
         right="绑定域与目录、声明 UTF-8、再设默认域",
         wrong=["三行顺序可任意调换，效果完全一样",
                "只需 textdomain，前两行是 autotools 专用可删",
                "应放在 make_window_and_run 之后，否则窗口标题不译"],
         why="Marking strings 与示例 main.cc 都是这三行。示例还可从配置文件改 LANG（文中说明非常规；多数程序沿用用户环境）。窗口标题等用 _() 包住的字符串才会被替换。",
         ref="Example main.cc：bindtextdomain / codeset / textdomain"),
]

CHECKPOINT = [
    dict(id="in27-cp-1", pos=0, locator="官方节页 sec-i18n-marking-strings",
         stem="从提取到安装，翻译文件扩展名大致经历怎样的变化？",
         right=".pot → 各语言 .po → 安装时编成 .mo",
         wrong=["先把 .mo 交给译者改，再合并回源码里的 .pot 模板",
                "始终只有 .po，运行时 gettext 直接解析该文本格式",
                ".ui 文件本身就是最终安装到系统里的二进制译文"],
         why="原文：xgettext/intltool-update 抽出 .pot；译者复制为 localename.po；安装时 .po 转成二进制 .mo（如 /usr/share/locale/）。运行时按用户 locale 查 .mo，找不到则用原文。",
         ref="综合 How gettext works：.pot / .po / .mo"),
    dict(id="in27-cp-2", pos=2, locator="官方节页 sec-i18n-pitfalls 与 sec-i18n-expecting-utf8",
         stem="同一英文词在不同语境含义不同时，推荐怎么标可译串？",
         code="""
Glib::ustring text(C_("noun", "jumps"));""",
         right="用 C_() 带上下文，避免两个相同的 _(\"jumps\")",
         wrong=["重复写两次 _(\"jumps\")，gettext 会自动分流语境",
                "只能改用 sprintf 拼出 jumps[noun] 再整体翻译",
                "把词写进注释，运行时用空字符串占位即可"],
         why="原文：英文相同但语义不同时，用英文字符串当查找键会冲突。可用 jumps[noun]/jumps[verb] 再剥标签，或更方便地用 C_() 代替 _()。日常文本用 Glib::ustring，勿按字节假设。",
         ref="综合 Pitfalls：C_()；Expecting UTF8：ustring"),
]

if __name__ == "__main__":
    inpage = [build(s) for s in INPAGE]
    cp = [build(s) for s in CHECKPOINT]
    report(inpage + cp)
