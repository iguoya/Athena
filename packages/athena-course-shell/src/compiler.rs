//! 本机 C++ 编译器的探测与命令构造。
//!
//! 实验要能「点一下就编译运行」，所以得用使用者机器上**已经有**的编译器。
//! GCC / Clang 一族自带完整环境，找到就能用；MSVC 不行——`cl.exe` 必须在
//! Developer Command Prompt 的环境里才找得到标准库头文件，而 GUI 应用是从
//! 启动器拉起来的，不在那个环境里。所以 MSVC 这条路要自己把环境备齐。
//!
//! 这是 ADR 0047 说的「这个平台真的提供了别处没有的能力」那一类平台代码：
//! `vswhere` / `vcvars64.bat` 只在 Windows 上存在，也只服务 Windows。分支关在
//! 本模块内，调用方只看见 `detect()` 和 `Compiler`。

use std::path::{Path, PathBuf};
use std::process::Command;

/// 一个可用的本机 C++ 编译器。
pub enum Compiler {
    /// GCC / Clang 一族：`-std=c++20 -o out` 那一套，环境自带。
    GnuLike { program: String },
    /// MSVC：参数是 `/std:c++20 /Fe:out` 另一套，而且要带上 vcvars 的环境变量。
    // 非 Windows 上 detect_msvc() 恒为 None，这个变体自然构造不出来，不是死代码。
    #[cfg_attr(not(windows), allow(dead_code))]
    Msvc {
        program: PathBuf,
        env: Vec<(String, String)>,
    },
}

impl Compiler {
    /// 给人看的名字，编译日志里会显示。
    pub fn label(&self) -> String {
        match self {
            Compiler::GnuLike { program } => program.clone(),
            Compiler::Msvc { .. } => "cl.exe (MSVC)".to_string(),
        }
    }

    /// 可执行产物该叫什么。Windows 上不带 .exe 的话，生成和执行都容易出岔子。
    pub fn artifact_name(&self) -> &'static str {
        if cfg!(windows) {
            "a.exe"
        } else {
            "a.out"
        }
    }

    /// 组装一条编译命令（单文件，课程实验用）。两族编译器的参数完全不同，映射集中在这里。
    pub fn compile_command(&self, src: &Path, out: &Path, include: Option<&Path>) -> Command {
        let includes: Vec<&Path> = include.into_iter().collect();
        self.compile_command_multi(&[src], out, &includes, None)
    }

    /// 多文件版（历史归档案例用，ADR 0176）：把 `srcs` 一起编译链接。
    ///
    /// - 全是 `.c` 时按 C 编译（GCC/Clang 换成 C 驱动，MSVC 按扩展名自动识别），不传
    ///   `-std=c++..`；混有 `.cpp` 就整体按 C++ 编（g++ 对 `.c` 也当 C++，与情境篇三一致）。
    /// - `std` 为 `None` 用课程默认（C++20）；归档的老代码可能要 `c++11` / `c++14`，由条目声明，
    ///   调用方先用 [`is_known_std`] 过滤，这里不再校验。
    pub fn compile_command_multi(
        &self,
        srcs: &[&Path],
        out: &Path,
        includes: &[&Path],
        std: Option<&str>,
    ) -> Command {
        let pure_c = !srcs.is_empty()
            && srcs
                .iter()
                .all(|s| s.extension().and_then(|e| e.to_str()) == Some("c"));
        match self {
            Compiler::GnuLike { program } => {
                let mut cmd = Command::new(if pure_c { c_driver(program) } else { program.clone() });
                match (pure_c, std) {
                    (true, Some(s)) => {
                        cmd.arg(format!("-std={s}"));
                    }
                    (true, None) => {}
                    (false, s) => {
                        cmd.arg(format!("-std={}", s.unwrap_or("c++20")));
                    }
                }
                cmd.arg("-O0").arg("-Wall").arg("-Wextra");
                // 并发实验用 std::thread：旧版 glibc 不加 -pthread 会链接失败；
                // MinGW 与 macOS 的 clang 都接受这个参数，统一加上免得分平台。
                // 原先只有 design-patterns 加，其余五个应用各抄一份时漏了。
                cmd.arg("-pthread");
                for s in srcs {
                    cmd.arg(s);
                }
                cmd.arg("-o").arg(out);
                for dir in includes {
                    cmd.arg(format!("-I{}", dir.display()));
                }
                if pure_c && !cfg!(windows) {
                    // 老 C 示例常直接用 <math.h>；Windows 的 CRT 自带，不需要也不认 -lm。
                    cmd.arg("-lm");
                }
                cmd
            }
            Compiler::Msvc { program, env } => {
                let mut cmd = Command::new(program);
                // /nologo 去掉版权横幅，否则每次编译日志都顶着两行噪音。
                // /EHsc 打开标准 C++ 异常模型——MSVC 默认不开，标准库一用就警告。
                // /Od 对应 -O0，/W4 大致对应 -Wall -Wextra。
                cmd.arg("/nologo").arg("/EHsc").arg("/Od").arg("/W4");
                if !pure_c {
                    cmd.arg(format!("/std:{}", msvc_std(std.unwrap_or("c++20"))));
                }
                for s in srcs {
                    cmd.arg(s);
                }
                // /Fe: 指定产物；/Fo: 指定中间 .obj，否则它会散在当前目录里。
                cmd.arg(format!("/Fe:{}", out.display()));
                if let Some(parent) = out.parent() {
                    cmd.arg(format!("/Fo:{}\\", parent.display()));
                }
                for dir in includes {
                    cmd.arg(format!("/I{}", dir.display()));
                }
                for (key, value) in env {
                    cmd.env(key, value);
                }
                cmd
            }
        }
    }
}

/// 归档条目允许声明的语言标准。白名单：这个字符串会拼进编译命令行。
pub fn is_known_std(s: &str) -> bool {
    matches!(
        s,
        "c++11" | "c++14" | "c++17" | "c++20" | "c++23" | "c89" | "c99" | "c11" | "c17" | "gnu11" | "gnu17"
    )
}

/// 给 C++ 驱动找配套的 C 驱动：`g++` → `gcc`、`clang++` → `clang`；`c++` 是个别名，在
/// MinGW 上没有对应的 `cc`，所以依次试 `cc`、`gcc`、`clang`。一个都起不来就退回 C++ 驱动
/// 自己（g++ 把 `.c` 当 C++ 编，老 C 示例大多仍能过，且日志里会看到真实的报错）。
fn c_driver(cxx: &str) -> String {
    let candidates: &[&str] = match cxx {
        "g++" => &["gcc"],
        "clang++" => &["clang"],
        "c++" => &["cc", "gcc", "clang"],
        _ => &[],
    };
    candidates
        .iter()
        .find(|c| {
            Command::new(c)
                .arg("--version")
                .output()
                .map(|o| o.status.success())
                .unwrap_or(false)
        })
        .map(|c| c.to_string())
        .unwrap_or_else(|| cxx.to_string())
}

/// MSVC 的 `/std:` 只认 c++14 / c++17 / c++20 / c++latest；更老的标准向上取最近一档。
fn msvc_std(std: &str) -> &'static str {
    match std {
        "c++11" | "c++14" => "c++14",
        "c++17" => "c++17",
        "c++23" => "c++latest",
        _ => "c++20",
    }
}

/// 找一个能用的编译器。
///
/// 顺序是有意的：GCC / Clang 自带环境、启动最快，优先；都没有时才去翻 MSVC，
/// 因为那条路要跑 vswhere 和 vcvars，有几百毫秒的代价。
pub fn detect() -> Option<Compiler> {
    for candidate in ["c++", "clang++", "g++"] {
        if Command::new(candidate)
            .arg("--version")
            .output()
            .map(|o| o.status.success())
            .unwrap_or(false)
        {
            return Some(Compiler::GnuLike {
                program: candidate.to_string(),
            });
        }
    }
    detect_msvc()
}

/// 找不到编译器时给使用者的话。
///
/// 只写**查起来费事**的那部分：VS 要勾哪个工作负载、MSYS2 的包名叫什么。
/// 官网地址、「LLVM 带 clang++」这类常识不写——读者是开发者，写进去是把人
/// 当小白，反而淹没了真正有用的那一行。
pub fn install_hint() -> &'static str {
    if cfg!(windows) {
        "没找到 C++ 编译器。装 Visual Studio（勾「使用 C++ 的桌面开发」）、LLVM，\
         或 MSYS2 后 pacman -S mingw-w64-ucrt-x86_64-gcc。"
    } else if cfg!(target_os = "macos") {
        "没找到 C++ 编译器。xcode-select --install"
    } else {
        "没找到 C++ 编译器。apt install g++ 或 dnf install gcc-c++。"
    }
}

#[cfg(windows)]
fn detect_msvc() -> Option<Compiler> {
    // vswhere 跟 VS 安装器一起装，位置是固定的——这是微软给出的官方查找方式，
    // 比猜 VS 的安装路径可靠（版本、版次、盘符都可能不一样）。
    let program_files = std::env::var("ProgramFiles(x86)")
        .or_else(|_| std::env::var("ProgramFiles"))
        .ok()?;
    let vswhere = PathBuf::from(program_files)
        .join("Microsoft Visual Studio")
        .join("Installer")
        .join("vswhere.exe");
    if !vswhere.is_file() {
        return None;
    }

    let found = Command::new(&vswhere)
        .args([
            "-latest",
            "-products",
            "*",
            "-requires",
            "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
            "-property",
            "installationPath",
        ])
        .output()
        .ok()?;
    let install = String::from_utf8_lossy(&found.stdout).trim().to_string();
    if install.is_empty() {
        return None;
    }

    let vcvars = PathBuf::from(&install)
        .join("VC")
        .join("Auxiliary")
        .join("Build")
        .join("vcvars64.bat");
    if !vcvars.is_file() {
        return None;
    }

    // 让 vcvars 把环境布置好，再把结果原样打出来。`set` 的输出是 KEY=VALUE 一行一条，
    // 解析出来交给后续的 cl.exe——这样只付一次 vcvars 的代价。
    let dumped = Command::new("cmd")
        .args(["/C", &format!("\"{}\" >nul 2>&1 && set", vcvars.display())])
        .output()
        .ok()?;
    let text = String::from_utf8_lossy(&dumped.stdout);
    let env: Vec<(String, String)> = text
        .lines()
        .filter_map(|line| line.split_once('='))
        .map(|(k, v)| (k.to_string(), v.to_string()))
        .collect();
    if env.is_empty() {
        return None;
    }

    // cl.exe 在 vcvars 布好的 PATH 里；顺着那份 PATH 找它的绝对路径，
    // 免得执行时还要依赖进程自身的 PATH。
    let path = env
        .iter()
        .find(|(k, _)| k.eq_ignore_ascii_case("PATH"))
        .map(|(_, v)| v.clone())?;
    let cl = std::env::split_paths(&path)
        .map(|dir| dir.join("cl.exe"))
        .find(|candidate| candidate.is_file())?;

    Some(Compiler::Msvc { program: cl, env })
}

#[cfg(not(windows))]
fn detect_msvc() -> Option<Compiler> {
    None
}
