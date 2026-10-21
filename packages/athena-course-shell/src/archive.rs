//! 历史归档案例的读取与多文件运行（ADR 0176）。
//!
//! 归档案例是从旧 GitHub 仓库搬来的**原样**代码，一个案例就是 `content/cases/arc_*` 下的一个
//! 目录，里面保留原来的多文件结构（`.h` / `.cpp` / `.c` 与子目录）。与课程实验的单文件
//! `compile_and_run` 不同，这里：
//!
//! - 整个案例目录拷到临时目录再编译，不碰 `content/cases/`（理由同 `compile_and_run`：
//!   Vite 监视那个目录，写文件会整页刷新）；
//! - 编译清单里的 `sources` 由条目声明，不靠“目录里所有 .cpp”猜——旧目录里常混着没用的文件；
//! - 老程序常有死循环、等输入、常驻服务，所以运行有**超时**，到点杀掉并如实说明；
//! - 只读：没有保存入口，原代码不被学习者改动，批注才是这里的内容。

use crate::compiler;
use serde::Serialize;
use std::fs;
use std::io::{Read, Write};
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::time::{Duration, Instant};

/// 单个案例最多读多少个文本文件、单文件最大字节数：防止误把大目录整个塞进界面。
const MAX_FILES: usize = 300;
const MAX_FILE_BYTES: u64 = 256 * 1024;
/// 一次运行的墙钟上限。
pub const RUN_TIMEOUT: Duration = Duration::from_secs(10);
const OUTPUT_LIMIT: usize = 200_000;

/// 当作文本展示的扩展名；其余（图片、二进制）不读。
const TEXT_EXT: &[&str] = &[
    "c", "h", "cpp", "cc", "cxx", "hpp", "hh", "s", "asm", "txt", "md", "pro", "pri", "qrc", "ui", "qml", "js", "json",
    "py", "cmake", "mk", "glade", "xml", "cgi", "sh", "css", "html",
];

#[derive(Serialize)]
pub struct CaseFile {
    /// 相对案例目录的路径，统一用 `/` 分隔。
    pub path: String,
    pub text: String,
}

#[derive(Serialize)]
pub struct ArchiveRun {
    /// 编译通过且进程以 0 退出。
    pub ok: bool,
    pub compiled: bool,
    pub timed_out: bool,
    pub exit_code: Option<i32>,
    pub compile_log: String,
    pub stdout: String,
    pub stderr: String,
    pub duration_ms: u128,
}

/// 案例内的相对路径：非空、`/` 分隔、每段都是安全单段名字。禁止绝对路径与 `..`。
pub fn is_safe_rel_path(rel: &str, plain: impl Fn(&str) -> bool) -> bool {
    !rel.is_empty() && !rel.starts_with('/') && rel.split('/').all(&plain)
}

fn is_text_file(path: &Path) -> bool {
    path.extension()
        .and_then(|e| e.to_str())
        .map(|e| TEXT_EXT.contains(&e.to_ascii_lowercase().as_str()))
        .unwrap_or(false)
        || matches!(path.file_name().and_then(|n| n.to_str()), Some("Makefile" | "CMakeLists.txt" | "README"))
}

fn collect(dir: &Path, base: &Path, out: &mut Vec<CaseFile>) {
    let Ok(rd) = fs::read_dir(dir) else { return };
    let mut entries: Vec<_> = rd.flatten().collect();
    entries.sort_by_key(|e| e.file_name());
    for e in entries {
        if out.len() >= MAX_FILES {
            return;
        }
        let path = e.path();
        let Ok(meta) = e.metadata() else { continue };
        if meta.is_dir() {
            collect(&path, base, out);
        } else if meta.len() <= MAX_FILE_BYTES && is_text_file(&path) {
            let Ok(bytes) = fs::read(&path) else { continue };
            // 旧代码多为 UTF-8 或 GBK：非 UTF-8 的用有损解码，宁可显示成问号也不丢文件。
            let text = String::from_utf8_lossy(&bytes).replace("\r\n", "\n");
            let rel = path
                .strip_prefix(base)
                .unwrap_or(&path)
                .to_string_lossy()
                .replace('\\', "/");
            out.push(CaseFile { path: rel, text });
        }
    }
}

/// 读出案例目录下全部文本文件，按路径排序。
pub fn list_case_files(case_dir: &Path) -> Vec<CaseFile> {
    let mut out = Vec::new();
    collect(case_dir, case_dir, &mut out);
    out
}

fn copy_dir(from: &Path, to: &Path) -> std::io::Result<()> {
    fs::create_dir_all(to)?;
    for e in fs::read_dir(from)?.flatten() {
        let (src, dst) = (e.path(), to.join(e.file_name()));
        if e.metadata()?.is_dir() {
            copy_dir(&src, &dst)?;
        } else {
            fs::copy(&src, &dst)?;
        }
    }
    Ok(())
}

fn clip(mut s: String) -> String {
    if s.len() > OUTPUT_LIMIT {
        let mut cut = OUTPUT_LIMIT;
        while !s.is_char_boundary(cut) {
            cut -= 1;
        }
        s.truncate(cut);
        s.push_str("\n…（输出已截断）\n");
    }
    s
}

/// 编译 `sources`（相对 `case_dir`，已校验）并运行，带超时。`work` 是调用方给的临时目录，
/// 函数结束时清理。
pub fn run_case(
    case_dir: &Path,
    work: &Path,
    sources: &[String],
    std: Option<&str>,
    stdin_text: Option<&str>,
    shared_include: Option<&Path>,
    timeout: Duration,
) -> Result<ArchiveRun, String> {
    let compiler = compiler::detect().ok_or_else(|| compiler::install_hint().to_string())?;
    if let Some(s) = std {
        if !compiler::is_known_std(s) {
            return Err(format!("不支持的语言标准：{s}"));
        }
    }
    let started = Instant::now();
    let result = (|| {
        copy_dir(case_dir, work).map_err(|e| format!("准备案例目录失败：{e}"))?;
        let srcs: Vec<PathBuf> = sources.iter().map(|s| work.join(s)).collect();
        for s in &srcs {
            if !s.is_file() {
                return Err(format!("案例里没有 {}", s.strip_prefix(work).unwrap_or(s).display()));
            }
        }
        let out = work.join(format!("__arc_{}", compiler.artifact_name()));
        // 头文件放在案例根或子目录里：把根与每个源文件所在目录都挂上 include 路径。
        let mut includes: Vec<PathBuf> = vec![work.to_path_buf()];
        for s in &srcs {
            if let Some(d) = s.parent() {
                if !includes.iter().any(|i| i == d) {
                    includes.push(d.to_path_buf());
                }
            }
        }
        if let Some(sh) = shared_include {
            includes.push(sh.to_path_buf());
        }
        let src_refs: Vec<&Path> = srcs.iter().map(|p| p.as_path()).collect();
        let inc_refs: Vec<&Path> = includes.iter().map(|p| p.as_path()).collect();
        let compile = compiler
            .compile_command_multi(&src_refs, &out, &inc_refs, std)
            .current_dir(work)
            .output()
            .map_err(|e| format!("启动 {} 失败：{e}", compiler.label()))?;
        let mut compile_log = String::from_utf8_lossy(&compile.stderr).to_string();
        compile_log.push_str(&String::from_utf8_lossy(&compile.stdout));
        if !compile.status.success() {
            return Ok(ArchiveRun {
                ok: false,
                compiled: false,
                timed_out: false,
                exit_code: None,
                compile_log: clip(compile_log),
                stdout: String::new(),
                stderr: String::new(),
                duration_ms: started.elapsed().as_millis(),
            });
        }

        let mut child = Command::new(&out)
            .current_dir(work)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .map_err(|e| format!("运行失败：{e}"))?;
        if let Some(mut si) = child.stdin.take() {
            // 老程序常等输入：给了就写，没给就立刻关闭，让它读到 EOF 而不是挂住。
            if let Some(t) = stdin_text {
                let _ = si.write_all(t.as_bytes());
            }
        }
        let mut so = child.stdout.take().ok_or("取不到标准输出")?;
        let mut se = child.stderr.take().ok_or("取不到标准错误")?;
        let t_out = std::thread::spawn(move || {
            let mut b = Vec::new();
            let _ = so.read_to_end(&mut b);
            b
        });
        let t_err = std::thread::spawn(move || {
            let mut b = Vec::new();
            let _ = se.read_to_end(&mut b);
            b
        });
        let mut timed_out = false;
        let status = loop {
            match child.try_wait().map_err(|e| e.to_string())? {
                Some(st) => break st,
                None if started.elapsed() > timeout => {
                    timed_out = true;
                    let _ = child.kill();
                    break child.wait().map_err(|e| e.to_string())?;
                }
                None => std::thread::sleep(Duration::from_millis(20)),
            }
        };
        let stdout = String::from_utf8_lossy(&t_out.join().unwrap_or_default()).to_string();
        let stderr = String::from_utf8_lossy(&t_err.join().unwrap_or_default()).to_string();
        Ok(ArchiveRun {
            ok: status.success() && !timed_out,
            compiled: true,
            timed_out,
            exit_code: status.code(),
            compile_log: clip(compile_log),
            stdout: clip(stdout),
            stderr: clip(stderr),
            duration_ms: started.elapsed().as_millis(),
        })
    })();
    let _ = fs::remove_dir_all(work);
    result
}

#[cfg(test)]
mod tests {
    use super::*;

    fn plain(s: &str) -> bool {
        !s.is_empty() && s != "." && s != ".." && s.chars().all(|c| c.is_ascii_alphanumeric() || "_-.".contains(c))
    }

    #[test]
    fn 相对路径只认安全的多段() {
        for ok in ["main.cpp", "Adapter/Adapter.cpp", "a/b/c.h"] {
            assert!(is_safe_rel_path(ok, plain), "{ok} 应合法");
        }
        for bad in ["", "/etc/passwd", "../x.cpp", "a/../b.cpp", "a//b.cpp", "a\\b.cpp", "C:/x.c"] {
            assert!(!is_safe_rel_path(bad, plain), "{bad:?} 应被拒绝");
        }
    }

    #[test]
    fn 文本文件判断() {
        assert!(is_text_file(Path::new("a/B.CPP")));
        assert!(is_text_file(Path::new("CMakeLists.txt")));
        assert!(is_text_file(Path::new("Makefile")));
        assert!(!is_text_file(Path::new("pic.bmp")));
        assert!(!is_text_file(Path::new("a.out")));
    }

    #[test]
    fn 多文件案例能编译运行并带超时() {
        // 本机没有编译器时跳过（CI 的各平台都装了；基线见 ADR 0057）。
        if compiler::detect().is_none() {
            return;
        }
        let base = std::env::temp_dir().join(format!("arc-test-{}", std::process::id()));
        let case = base.join("case");
        fs::create_dir_all(case.join("sub")).unwrap();
        fs::write(case.join("sub/util.h"), "int twice(int x);\n").unwrap();
        fs::write(case.join("sub/util.cpp"), "#include \"util.h\"\nint twice(int x){return x*2;}\n").unwrap();
        fs::write(
            case.join("main.cpp"),
            "#include <cstdio>\n#include \"sub/util.h\"\nint main(){std::printf(\"%d\\n\", twice(21));return 0;}\n",
        )
        .unwrap();
        fs::write(case.join("spin.cpp"), "int main(){for(;;){}}\n").unwrap();

        let r = run_case(
            &case,
            &base.join("w1"),
            &["main.cpp".into(), "sub/util.cpp".into()],
            None,
            None,
            None,
            RUN_TIMEOUT,
        )
        .unwrap();
        assert!(r.compiled && r.ok, "{}", r.compile_log);
        assert_eq!(r.stdout.trim(), "42");

        let bad = run_case(&case, &base.join("w2"), &["nope.cpp".into()], None, None, None, RUN_TIMEOUT);
        assert!(bad.is_err());

        // 死循环要被杀掉，且如实标 timed_out（老程序里常见）。
        let spin = run_case(&case, &base.join("w3"), &["spin.cpp".into()], None, None, None, Duration::from_millis(700)).unwrap();
        assert!(spin.compiled && spin.timed_out && !spin.ok);

        // C 示例按 C 编译，并可声明标准。
        fs::write(case.join("hello.c"), "#include <stdio.h>
int main(void){puts(\"hi\");return 0;}
").unwrap();
        let c = run_case(&case, &base.join("w4"), &["hello.c".into()], Some("c11"), None, None, RUN_TIMEOUT).unwrap();
        assert!(c.ok, "{}", c.compile_log);
        assert_eq!(c.stdout.trim(), "hi");
        let _ = fs::remove_dir_all(&base);
    }
}
