//! 本机 C++ 编译器的探测与命令构造。
//!
//! 实验要能点一下就编译运行，用机器上已经有的编译器。GCC / Clang 自带环境；
//! MSVC 的 cl.exe 必须先经过 vcvars，GUI 进程不在那个环境里，所以这条路自己备环境。
//! 平台分支关在本模块里。

use std::path::{Path, PathBuf};
use std::process::Command;

pub enum Compiler {
    GnuLike { program: String },
    #[cfg_attr(not(windows), allow(dead_code))]
    Msvc {
        program: PathBuf,
        env: Vec<(String, String)>,
    },
}

impl Compiler {
    pub fn label(&self) -> String {
        match self {
            Compiler::GnuLike { program } => program.clone(),
            Compiler::Msvc { .. } => "cl.exe (MSVC)".to_string(),
        }
    }

    pub fn artifact_name(&self) -> &'static str {
        if cfg!(windows) {
            "a.exe"
        } else {
            "a.out"
        }
    }

    pub fn compile_command(&self, src: &Path, out: &Path) -> Command {
        match self {
            Compiler::GnuLike { program } => {
                let mut cmd = Command::new(program);
                cmd.arg("-std=c++20")
                    .arg("-O0")
                    .arg("-Wall")
                    .arg("-Wextra")
                    .arg(src)
                    .arg("-o")
                    .arg(out);
                cmd
            }
            Compiler::Msvc { program, env } => {
                let mut cmd = Command::new(program);
                cmd.arg("/nologo")
                    .arg("/std:c++20")
                    .arg("/EHsc")
                    .arg("/Od")
                    .arg("/W4")
                    .arg(src)
                    .arg(format!("/Fe:{}", out.display()));
                if let Some(parent) = out.parent() {
                    cmd.arg(format!("/Fo:{}\\", parent.display()));
                }
                for (key, value) in env {
                    cmd.env(key, value);
                }
                cmd
            }
        }
    }
}

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
