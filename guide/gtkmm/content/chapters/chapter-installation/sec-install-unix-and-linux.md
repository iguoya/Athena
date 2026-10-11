---
chapter: chapter-installation
section: sec-install-unix-and-linux
upstream-sha: ad3f3718776091e0d2b1a7fbf13c7fb5373bb43461c6dbffe33971eadbe75233
upstream-commit: b89295e22598db8697d1aa22dd528a103d956c9b
---

<!-- 来源：Programming with gtkmm 4 · Unix and Linux
     分页严格跟随官方仓库结构（每节一页，对应官网 sec-sec-install-unix-and-linux 页面）。
     引用块为英文原文，紧随段落为中文翻译；代码块照录不译。
     upstream-sha 变化即表示官方原文已改，本稿需要复核。 -->

### Prebuilt Packages（预编译包）

> Recent versions of gtkmm are packaged by nearly every major Linux
> distribution these days. So, if you use Linux, you can probably get started
> with gtkmm by installing the package from the official repository for your
> distribution. Distributions that include gtkmm in their repositories
> include Debian, Ubuntu, Red Hat, Fedora, Mandriva, Suse, and many others.

如今几乎所有主流 Linux 发行版都打包了新版 gtkmm。如果你用 Linux，多半可以直接
从发行版的官方仓库安装 gtkmm 包来上手。仓库里带有 gtkmm 的发行版包括 Debian、
Ubuntu、Red Hat、Fedora、Mandriva、Suse 等等。

> The names of the gtkmm packages vary from distribution to distribution
> (e.g. libgtkmm-4.0-dev on Debian and Ubuntu or gtkmm4.0-devel on Red Hat
> and Fedora), so check with your distribution's package management program
> for the correct package name and install it like you would any other
> package.

gtkmm 包的名字因发行版而异（比如 Debian 和 Ubuntu 上是 libgtkmm-4.0-dev，
Red Hat 和 Fedora 上是 gtkmm4.0-devel），请用发行版的包管理器查一下正确的
包名，然后像安装其他包一样安装即可。

> The package names will not change when new API/ABI-compatible versions of
> gtkmm are released. Otherwise they would not be API/ABI-compatible. So
> don't be surprised, for instance, to find gtkmm 4.8 supplied by Debian's
> libgtkmm-4.0-dev package.

发布 API/ABI 兼容的新版本时，包名不会变——否则就谈不上 API/ABI 兼容了。所以
比如你发现 Debian 的 libgtkmm-4.0-dev 装的是 gtkmm 4.8，不必惊讶。

### Installing From Source（从源码安装）

> If your distribution does not provide a pre-built gtkmm package, or if you
> want to install a different version than the one provided by your
> distribution, you can also install gtkmm from source. The source code for
> gtkmm can be downloaded from https://download.gnome.org/sources/gtkmm/.

如果发行版没有提供预编译的 gtkmm 包，或者你想安装与发行版所提供的不同的版本，
也可以从源码安装。gtkmm 源码可从 https://download.gnome.org/sources/gtkmm/
下载。

> After you've installed all of the dependencies, download the gtkmm source
> code, unpack it, and change to the newly created directory. gtkmm can be
> built with Meson. See the README file in the gtkmm version you've
> downloaded.

装好全部依赖后，下载 gtkmm 源码、解压、进入新解出的目录。gtkmm 可以用 Meson
构建，具体见你所下载版本里的 README 文件。

> Remember that on a Unix or Linux operating system, you will probably need
> to be root to install software. The su or sudo command will allow you to
> enter the root password and have root status temporarily.

记住，在 Unix 或 Linux 操作系统上安装软件通常需要 root 权限。用 su 或 sudo
命令输入 root 密码，即可临时获得 root 身份。

> The configure script or meson will check to make sure all of the required
> dependencies are already installed. If you are missing any dependencies, it
> will exit and display an error.

configure 脚本或 meson 会检查所需的依赖是否都已安装；缺了任何一项，它都会
退出并显示错误。

> By default, gtkmm if built with Meson or Autotools, will be installed under
> the /usr/local directory. On some systems you may need to install to a
> different location. For instance, on Red Hat Linux systems you might use
> the --prefix option with configure, like one of:

用 Meson 或 Autotools 构建的 gtkmm 默认安装到 /usr/local 目录下。在某些系统
上你可能需要装到别的位置——比如在 Red Hat Linux 系统上，可以在 configure 时
用 --prefix 选项，例如：

```bash
# meson setup --prefix=/usr <builddir> <srcdir>
# meson configure --prefix=/usr
# ./configure --prefix=/usr
```


> You should be very careful when installing to standard system prefixes such
> as /usr. Linux distributions install software packages to /usr, so
> installing a source package to this prefix could corrupt or conflict with
> software installed using your distribution's package-management system.
> Ideally, you should use a separate prefix for all software you install from
> source.

往 /usr 这类标准系统前缀里安装时要格外小心：Linux 发行版把软件包装在 /usr，
把源码包装到这个前缀可能破坏或冲突于包管理系统装好的软件。理想做法是给所有
从源码安装的软件用一个单独的前缀。

> If you want to help develop gtkmm or experiment with new features, you can
> also install gtkmm from git. Most users will never need to do this, but if
> you're interested in helping with gtkmm development, see the Working with
> gtkmm's Source Code appendix.

如果想参与 gtkmm 开发或试用新特性，也可以从 git 安装。大多数用户永远用不着
这么做，但如果你有兴趣为 gtkmm 出力，请参阅附录「Working with gtkmm's Source
Code」。
