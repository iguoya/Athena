"""第 2 章（chapter-installation）测验标准版草稿：sec-installation-dependencies /
sec-install-unix-and-linux / sec-packages-windows。

包名、版本号、命令与前缀的全部断言以本章快照英文原文为准；本章无可运行代码，
代码题均为命令 / 包名 / 配置片段。
"""
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2] / "tools"))
from quizlib import build, report

DEP, LIN, WIN = "sec-installation-dependencies", "sec-install-unix-and-linux", "sec-packages-windows"

INPAGE = [
    dict(id="inst-dep-2", page=DEP, pos=0, lang="bash",
         stem="安装 gtkmm-4.0 前先核对待装依赖。按本章列出的清单，下面哪项不在其中？",
         code="""
# 待装依赖清单：
#   sigc++-3.0    gtk4          glibmm-2.68
#   cairomm-1.16  pangomm-2.48  qt6
#   pkg-config    glib-2.0      pango
#   cairo         gdk-pixbuf-2.0   graphene-1.0""",
         right="qt6",
         wrong=["sigc++-3.0", "glibmm-2.68", "pkg-config"],
         why="文档列出的 gtkmm-4.0 直接依赖是 sigc++-3.0、gtk4、glibmm-2.68、cairomm-1.16、pangomm-2.48；它们自身还依赖 pkg-config、glib-2.0、pango、cairo、gdk-pixbuf-2.0、graphene-1.0。qt6 属于另一套工具集，与 gtkmm 无关。",
         ref="sec-installation-dependencies：两段依赖清单"),
    dict(id="inst-lin-1", page=LIN, pos=2, lang="bash",
         stem="在两台机器上分别用发行版仓库装 gtkmm 4，两条命令的空白处该怎么填？",
         code="""
# Debian / Ubuntu
$ sudo apt install ____
# Red Hat / Fedora
$ sudo dnf install ____""",
         right="libgtkmm-4.0-dev；gtkmm4.0-devel",
         wrong=["gtkmm4.0-devel；libgtkmm-4.0-dev",
                "libgtkmm4-dev；gtkmm4-devel",
                "gtkmm-dev；gtkmm-devel"],
         why="包名因发行版而异，文档给出的正是 Debian/Ubuntu 的 libgtkmm-4.0-dev 与 Red Hat/Fedora 的 gtkmm4.0-devel。名字里的 4.0 是 API/ABI 名，不是可以省略的版本号，两个发行版的命名习惯也不同。",
         ref="sec-install-unix-and-linux 预编译包：两发行版包名原文"),
    dict(id="inst-lin-2", page=LIN, pos=1,
         stem="Debian 的 libgtkmm-4.0-dev 包更新后装的是 gtkmm 4.8，包名却没变。为什么？",
         right="4.8 与包名承诺的 API/ABI 兼容；兼容版本不改包名",
         wrong=["Debian 约定主版本号不变时包名不变，gtkmm 照做",
                "打包者疏忽忘了改名，正确名应为 libgtkmm-4.8-dev",
                "包名跟 GTK 主版本走，GTK 4 内部升级不换名字"],
         why="原文：API/ABI 兼容的新版本发布时，包名不会变——否则它们就不是 API/ABI 兼容的了。所以 libgtkmm-4.0-dev 装 gtkmm 4.8 是正常现象，「忘了改名」是常见误解。",
         ref="sec-install-unix-and-linux：package names will not change when new API/ABI-compatible versions"),
    dict(id="inst-lin-3", page=LIN, pos=3, lang="bash",
         stem="从源码构建 gtkmm 时写下这样的前缀配置。本章对装到 /usr 的警告是？",
         code="""
# meson setup --prefix=/usr <builddir> <srcdir>
# meson configure --prefix=/usr
# ./configure --prefix=/usr""",
         right="会与包管理系统装的软件冲突甚至损坏，源码安装应用独立前缀",
         wrong=["meson 不认 /usr 以外的前缀，示例才都写它",
                "装进 /usr 的库普通用户无法读取，程序都得提权运行",
                "/usr 下的文件重启后会丢失，持久化要选 /usr/local"],
         why="原文警告：装到 /usr 这类标准系统前缀要非常小心，发行版的软件包都装在那里，源码包装进去可能损坏或与之冲突；理想做法是所有源码安装的软件都用独立前缀。默认安装前缀其实是 /usr/local，/usr 并不会因重启丢失文件。",
         ref="sec-install-unix-and-linux：标准系统前缀警告与默认 /usr/local"),
    dict(id="inst-lin-4", page=LIN, pos=0, lang="bash",
         stem="机器上还没装 cairomm。在这样的机器上运行 meson setup 配置 gtkmm 源码，会发生什么？",
         code="""
$ meson setup builddir   # 在解压后的 gtkmm 源码目录里""",
         right="检查依赖时发现缺 cairomm，退出并显示错误",
         wrong=["只提示警告继续配置，到编译阶段才报缺库",
                "自动下载并安装缺失的 cairomm 后接着配置",
                "跳过缺失依赖，构建出不含 cairo 支持的 gtkmm"],
         why="原文：configure 脚本或 meson 会检查所有必需依赖是否已经装好，缺了就退出并显示错误，把依赖装好再重新运行即可。meson 既不自动下载依赖，也不会静默降级出一个功能残缺的 gtkmm。",
         ref="sec-install-unix-and-linux：meson/configure 的依赖检查"),
    dict(id="inst-win-2", page=WIN, pos=1,
         stem="想在 Microsoft Windows 上装 gtkmm 开发环境，本章给的说法是？",
         right="没有标准的开发库安装体系，按专门页面与附录的说明装",
         wrong=["Windows 完全不受支持，gtkmm 只在 Linux 上发行维护",
                "用系统自带的一条命令即可装齐，与 Linux 仓库一样",
                "支持得看运气，官方明确说过 Windows 版已停止维护"],
         why="原文：GTK 与 gtkmm 在设计上就与 Microsoft Windows 配合良好，开发者鼓励在 win32 平台使用；但 Windows 没有标准的开发库安装体系，具体安装要看 Windows Installation 页面（已略显过时）或 gtkmm and Win32 附录。「不支持 Windows」「停止维护」都与原文相反。",
         ref="sec-packages-windows 全节：no standard installation system for development libraries"),
]

CHECKPOINT = [
    dict(id="inst-cp-2", pos=2, locator="官方节页 sec-install-unix-and-linux",
         stem="Fedora 仓库里的 gtkmm 比想要的旧，同学从官方源码包安装新版，写下这些命令。问题出在哪？",
         code="""
$ tar -xf gtkmm-4.14.0.tar.xz
$ cd gtkmm-4.14.0
$ meson setup builddir --prefix=/usr
$ sudo meson install -C builddir""",
         right="--prefix=/usr 与 dnf 的地盘冲突，应换独立前缀",
         wrong=["meson install 用了 sudo，安装本不需要 root 权限",
                "gtkmm 源码不能用 meson 编译，得换 ./configure",
                "版本号 4.14.0 应去掉，目录名必须与仓库包一致"],
         why="文档警告：/usr 是发行版包管理系统装软件的地方，把源码包装到这种标准系统前缀可能损坏或冲突 dnf 装的 gtkmm4.0-devel，理想做法是源码安装用独立前缀（默认 /usr/local 也是独立前缀）。安装需要 root、用 sudo 是原文明说的正常做法；用 Meson 构建也是文档写明的路径。",
         ref="综合 sec-install-unix-and-linux：源码下载与 Meson 构建、标准前缀警告、su/sudo"),
]

if __name__ == "__main__":
    report([build(s) for s in INPAGE] + [build(s) for s in CHECKPOINT])
