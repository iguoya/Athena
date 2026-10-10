//! 本机资料（ADR 0019、0025）：真题、教材与引用了未授权来源的考研英语二题目只在本机，
//! 不进仓库、不进安装包，所以不能像其余内容那样在构建时打进前端，只能运行时读。
//!
//! 位置：开发版直接用仓库里的 `content/private/`（资料本来就放在那里）；安装版用用户数据
//! 目录下的 `private/`，由「导入本地资料」从别处（例如开发机拷来的 `content/private`）复制进来。

use std::fs;
use std::path::{Path, PathBuf};

use serde::Serialize;
use tauri::{AppHandle, Manager};

/// 磨砚带过来的作者侧参考资料（原样转存的词表、句库），几十兆、不是题，不读给前端。
const SKIP_DIRS: [&str; 1] = ["sources"];

#[derive(Serialize)]
pub struct PrivateFile {
    /// 相对 `english2/` 的路径，与公开内容同一套路径，前端按路径合并。
    path: String,
    text: String,
}

#[derive(Serialize)]
pub struct PrivateStatus {
    root: String,
    /// 开发版读的是仓库里的 content/private/，导入只影响安装版那份。
    dev: bool,
    english2_files: usize,
}

fn installed_root(app: &AppHandle) -> Result<PathBuf, String> {
    app.path()
        .app_data_dir()
        .map(|dir| dir.join("private"))
        .map_err(|error| format!("找不到用户数据目录：{error}"))
}

fn private_root(app: &AppHandle) -> Result<(PathBuf, bool), String> {
    #[cfg(debug_assertions)]
    {
        let dev = Path::new(env!("CARGO_MANIFEST_DIR")).join("../content/private");
        if dev.is_dir() {
            return Ok((dev, true));
        }
    }
    installed_root(app).map(|root| (root, false))
}

/// `dir` 下的 .json 与 .md，路径相对 `base`、一律正斜杠（Windows 上也和前端的路径对得上）。
fn collect(base: &Path, dir: &Path, out: &mut Vec<PathBuf>) -> std::io::Result<()> {
    for entry in fs::read_dir(dir)? {
        let path = entry?.path();
        if path.is_dir() {
            let top = path.strip_prefix(base).ok().and_then(|p| p.components().next());
            if dir == base && top.is_some_and(|c| SKIP_DIRS.iter().any(|s| c.as_os_str() == *s)) {
                continue;
            }
            collect(base, &path, out)?;
        } else if path.extension().is_some_and(|ext| ext == "json" || ext == "md") {
            out.push(path);
        }
    }
    Ok(())
}

fn relative(base: &Path, path: &Path) -> String {
    path.strip_prefix(base)
        .unwrap_or(path)
        .components()
        .map(|c| c.as_os_str().to_string_lossy())
        .collect::<Vec<_>>()
        .join("/")
}

#[tauri::command]
pub fn read_private_english2(app: AppHandle) -> Result<Vec<PrivateFile>, String> {
    let (root, _) = private_root(&app)?;
    let base = root.join("english2");
    if !base.is_dir() {
        return Ok(Vec::new());
    }
    let mut paths = Vec::new();
    collect(&base, &base, &mut paths).map_err(|error| format!("读不了 {}：{error}", base.display()))?;
    paths
        .into_iter()
        .map(|path| {
            let text = fs::read_to_string(&path).map_err(|error| format!("读不了 {}：{error}", path.display()))?;
            Ok(PrivateFile { path: relative(&base, &path), text })
        })
        .collect()
}

#[tauri::command]
pub fn private_status(app: AppHandle) -> Result<PrivateStatus, String> {
    let (root, dev) = private_root(&app)?;
    let base = root.join("english2");
    let mut paths = Vec::new();
    if base.is_dir() {
        collect(&base, &base, &mut paths).map_err(|error| error.to_string())?;
    }
    let english2_files = paths.iter().filter(|p| p.extension().is_some_and(|e| e == "json")).count();
    Ok(PrivateStatus { root: root.display().to_string(), dev, english2_files })
}

fn copy_tree(from: &Path, to: &Path) -> std::io::Result<usize> {
    fs::create_dir_all(to)?;
    let mut copied = 0;
    for entry in fs::read_dir(from)? {
        let entry = entry?;
        let target = to.join(entry.file_name());
        if entry.path().is_dir() {
            copied += copy_tree(&entry.path(), &target)?;
        } else {
            fs::copy(entry.path(), &target)?;
            copied += 1;
        }
    }
    Ok(copied)
}

/// 选中的文件夹可以是 `private` 本身，也可以是它的上一层（`content`）。复制进用户数据目录，
/// 同名文件覆盖、其余保留：分几次导入真题和英语二互不冲掉。
#[tauri::command]
pub fn import_private(app: AppHandle, from: String) -> Result<usize, String> {
    let picked = PathBuf::from(&from);
    let source = if picked.join("private").is_dir() { picked.join("private") } else { picked };
    let looks_right = ["english2", "exam", "textbook"].iter().any(|d| source.join(d).is_dir());
    if !looks_right {
        return Err(format!(
            "{} 里没有 english2、exam 或 textbook 文件夹，不像本机资料目录。请选开发机上的 content/private。",
            source.display()
        ));
    }
    let dest = installed_root(&app)?;
    copy_tree(&source, &dest).map_err(|error| format!("复制到 {} 失败：{error}", dest.display()))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn 只收题目文件_跳过参考资料_路径用正斜杠() {
        let base = std::env::temp_dir().join(format!("ascent-private-test-{}", std::process::id()));
        let _ = fs::remove_dir_all(&base);
        fs::create_dir_all(base.join("vocab/beginner")).unwrap();
        fs::create_dir_all(base.join("sources/reference")).unwrap();
        fs::write(base.join("vocab/beginner/generated-01.json"), "{}").unwrap();
        fs::write(base.join("passage.md"), "text").unwrap();
        fs::write(base.join("notes.txt"), "skip").unwrap();
        fs::write(base.join("sources/reference/kylebing.json"), "{}").unwrap();

        let mut paths = Vec::new();
        collect(&base, &base, &mut paths).unwrap();
        let mut rels: Vec<String> = paths.iter().map(|p| relative(&base, p)).collect();
        rels.sort();
        assert_eq!(rels, ["passage.md", "vocab/beginner/generated-01.json"]);
        fs::remove_dir_all(&base).unwrap();
    }
}
