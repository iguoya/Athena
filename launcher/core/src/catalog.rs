//! 安装模式的应用清单（ADR 0173）。
//!
//! 仓库模式从各应用的 `app.json` 现读清单；装在没有仓库的机器上，启动器靠编译期内嵌的
//! `launcher/core/catalog.json` 工作。它由 `launcher catalog` 从仓库生成并提交入库，只含
//! 发布清单（`scripts/release_apps.json`）里的应用，字段取展示与定位所需的——不含 `dev` 块。
//!
//! 过期由本模块的单元测试（`catalog_is_up_to_date`）拦住：CI 的启动器作业跑
//! `cargo test`，应用清单变了而没重新生成就红。

use std::path::{Path, PathBuf};

use serde::{Deserialize, Serialize};

use crate::manifest::{self, App, DevSpec, Install, Lifecycle, ProgressSpec};

/// 编译期内嵌的清单。
pub const EMBEDDED: &str = include_str!("../catalog.json");

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct CatalogEntry {
    pub id: String,
    pub title: String,
    pub summary: String,
    pub symbol: String,
    pub letter: String,
    pub accent: String,
    pub group: Option<String>,
    pub related: Vec<String>,
    pub evolves_from: Option<String>,
    pub parent: Option<String>,
    pub also_under: Vec<String>,
    pub also_in: Vec<String>,
    pub hidden: bool,
    /// active / built / archived（`Lifecycle::key`）。
    pub lifecycle: String,
    /// 发布清单里的 kind：tauri / ascent / cpp / driver / electron。决定安装模式能不能启动它。
    pub kind: String,
    /// Tauri 应用的 `productName`：Windows 的安装目录、macOS 的 `.app` 名都由它来。
    pub product_name: Option<String>,
    /// 可执行文件名（不含扩展名）：`mainBinaryName`，缺省取 `src-tauri/Cargo.toml` 的包名。
    pub main_binary: Option<String>,
    pub identifier: Option<String>,
    pub progress: Option<ProgressSpec>,
    /// 图标的 data URL（`icon.svg` 原样内嵌）：安装模式下没有文件可读。
    pub icon: Option<String>,
}

/// 发布清单里生成 catalog 要用的那几项。
struct ReleaseApp {
    id: String,
    kind: String,
    dir: String,
}

fn read_release_apps(repo: &Path) -> Result<Vec<ReleaseApp>, String> {
    let path = repo.join("scripts/release_apps.json");
    let text = std::fs::read_to_string(&path).map_err(|e| format!("读不到 {}：{e}", path.display()))?;
    let rows: Vec<serde_json::Value> =
        serde_json::from_str(&text).map_err(|e| format!("{} 不是合法 JSON：{e}", path.display()))?;
    rows.iter()
        .map(|row| {
            let field = |name: &str| {
                row.get(name)
                    .and_then(|v| v.as_str())
                    .map(str::to_string)
                    .ok_or_else(|| format!("release_apps.json 的条目缺 {name}：{row}"))
            };
            let id = field("id")?;
            let root = field("root")?;
            // dir 缺省为 <root>/<id>（与 scripts/release_plan.py 的 app_dir 同一规则）。
            let dir = row
                .get("dir")
                .and_then(|v| v.as_str())
                .map(str::to_string)
                .unwrap_or_else(|| format!("{root}/{id}"));
            Ok(ReleaseApp { id, kind: field("kind")?, dir })
        })
        .collect()
}

/// 从仓库生成清单。顺序跟发布清单一致，输出稳定。没有 `app.json` 的条目（启动器自己）跳过。
pub fn generate(repo: &Path) -> Result<Vec<CatalogEntry>, String> {
    let released = read_release_apps(repo)?;
    let apps = manifest::discover_all(repo);
    let mut entries = Vec::new();
    for release in released {
        let Some(app) = apps.iter().find(|app| app.id == release.id) else {
            continue;
        };
        let (product_name, main_binary, identifier) = if matches!(release.kind.as_str(), "tauri" | "ascent") {
            tauri_identity(&repo.join(&release.dir))
        } else {
            (None, None, None)
        };
        entries.push(CatalogEntry {
            id: app.id.clone(),
            title: app.title.clone(),
            summary: app.summary.clone(),
            symbol: app.symbol.clone(),
            letter: app.letter.clone(),
            accent: app.accent.clone(),
            group: app.group.clone(),
            related: app.related.clone(),
            evolves_from: app.evolves_from.clone(),
            parent: app.parent.clone(),
            also_under: app.also_under.clone(),
            also_in: app.also_in.clone(),
            hidden: app.hidden,
            lifecycle: app.lifecycle.key().to_string(),
            kind: release.kind,
            product_name,
            main_binary,
            identifier,
            progress: app.progress.clone(),
            icon: app.icon_file.as_deref().and_then(data_url),
        });
    }
    Ok(entries)
}

/// 读 `src-tauri/tauri.conf.json` 与 `Cargo.toml`，取安装位置要用的三样。
fn tauri_identity(app_dir: &Path) -> (Option<String>, Option<String>, Option<String>) {
    let conf: serde_json::Value = std::fs::read_to_string(app_dir.join("src-tauri/tauri.conf.json"))
        .ok()
        .and_then(|text| serde_json::from_str(&text).ok())
        .unwrap_or(serde_json::Value::Null);
    let text = |key: &str| conf.get(key).and_then(|v| v.as_str()).map(str::to_string);
    let product_name = text("productName");
    let main_binary = text("mainBinaryName").or_else(|| cargo_package_name(&app_dir.join("src-tauri/Cargo.toml")));
    (product_name, main_binary, text("identifier"))
}

/// `[package]` 段里的 `name`。只为取一个字符串，不为此引入 TOML 解析依赖。
fn cargo_package_name(path: &Path) -> Option<String> {
    let text = std::fs::read_to_string(path).ok()?;
    let mut in_package = false;
    for line in text.lines() {
        let line = line.trim();
        if line.starts_with('[') {
            in_package = line == "[package]";
            continue;
        }
        if in_package {
            if let Some(rest) = line.strip_prefix("name") {
                let value = rest.trim_start().strip_prefix('=')?.trim();
                return Some(value.trim_matches('"').to_string());
            }
        }
    }
    None
}

fn data_url(path: &Path) -> Option<String> {
    let mime = match path.extension()?.to_str()? {
        "svg" => "image/svg+xml",
        "png" => "image/png",
        _ => return None,
    };
    let bytes = std::fs::read(path).ok()?;
    Some(format!("data:{mime};base64,{}", base64(&bytes)))
}

/// 标准 base64（带补位）。图标是仅有的用途，不值得为此加依赖。
fn base64(bytes: &[u8]) -> String {
    const TABLE: &[u8; 64] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    let mut out = String::with_capacity(bytes.len().div_ceil(3) * 4);
    for chunk in bytes.chunks(3) {
        let b = [chunk[0], *chunk.get(1).unwrap_or(&0), *chunk.get(2).unwrap_or(&0)];
        let n = (u32::from(b[0]) << 16) | (u32::from(b[1]) << 8) | u32::from(b[2]);
        out.push(TABLE[(n >> 18) as usize & 63] as char);
        out.push(TABLE[(n >> 12) as usize & 63] as char);
        out.push(if chunk.len() > 1 { TABLE[(n >> 6) as usize & 63] as char } else { '=' });
        out.push(if chunk.len() > 2 { TABLE[n as usize & 63] as char } else { '=' });
    }
    out
}

/// 落盘的格式：缩进 2 空格的 JSON 数组，文件末尾一个换行。键序由结构体字段序固定。
pub fn to_json(entries: &[CatalogEntry]) -> String {
    let mut text = serde_json::to_string_pretty(entries).unwrap_or_else(|_| "[]".to_string());
    text.push('\n');
    text
}

pub fn catalog_path(repo: &Path) -> PathBuf {
    repo.join("launcher/core/catalog.json")
}

/// 写 `launcher/core/catalog.json`。
pub fn write(repo: &Path) -> Result<usize, String> {
    let entries = generate(repo)?;
    let path = catalog_path(repo);
    std::fs::write(&path, to_json(&entries)).map_err(|e| format!("写不了 {}：{e}", path.display()))?;
    Ok(entries.len())
}

/// 只核对不写。换行差异（Windows 检出可能是 CRLF）不算过期。
pub fn check(repo: &Path) -> Result<(), String> {
    let expected = to_json(&generate(repo)?);
    let path = catalog_path(repo);
    let actual = std::fs::read_to_string(&path).map_err(|e| format!("读不到 {}：{e}", path.display()))?;
    if actual.replace("\r\n", "\n") == expected {
        Ok(())
    } else {
        Err(format!("{} 和应用清单对不上，跑一次 `launcher catalog`。", path.display()))
    }
}

/// 内嵌清单。解析失败是构建期就该发现的错，所以不容忍：直接 panic 带上原因。
pub fn load_embedded() -> Vec<CatalogEntry> {
    serde_json::from_str(EMBEDDED).expect("launcher/core/catalog.json 不是合法的清单")
}

fn parse_lifecycle(key: &str) -> Lifecycle {
    match key {
        "built" => Lifecycle::Built,
        "archived" => Lifecycle::Archived,
        _ => Lifecycle::Active,
    }
}

/// 清单条目 → 启动器的 `App`。`locate` 回答「它装在哪」：装了就把安装目录当 `dir`，
/// 状态探测沿用「可执行文件路径落在 `match_prefix` 下」的老判据，不另造一套。
/// 没装的应用 `dir` 给一个不存在的相对路径，保证不会匹配到任何进程。
pub fn into_apps(entries: Vec<CatalogEntry>, locate: impl Fn(&CatalogEntry) -> Option<PathBuf>) -> Vec<App> {
    entries
        .into_iter()
        .map(|entry| {
            let supported = crate::installed::is_supported(&entry.kind);
            let exe = if supported { locate(&entry) } else { None };
            let dir = exe
                .as_deref()
                .and_then(Path::parent)
                .map(Path::to_path_buf)
                .unwrap_or_else(|| PathBuf::from("<未安装>").join(&entry.id));
            App {
                id: entry.id,
                title: entry.title,
                summary: entry.summary,
                symbol: entry.symbol,
                letter: entry.letter,
                accent: entry.accent,
                icon_file: None,
                icon_renders: Vec::new(),
                dir,
                dev: DevSpec { binary: entry.main_binary, ..DevSpec::default() },
                evolves_from: entry.evolves_from,
                group: entry.group,
                related: entry.related,
                parent: entry.parent,
                also_under: entry.also_under,
                also_in: entry.also_in,
                hidden: entry.hidden,
                lifecycle: parse_lifecycle(&entry.lifecycle),
                progress: entry.progress,
                install: Some(Install { installed: exe.is_some(), exe, supported, kind: entry.kind }),
                embedded_icon: entry.icon,
            }
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    fn repo_root() -> PathBuf {
        Path::new(env!("CARGO_MANIFEST_DIR")).join("../..").canonicalize().expect("仓库根")
    }

    #[test]
    fn base64_补位正确() {
        assert_eq!(base64(b""), "");
        assert_eq!(base64(b"f"), "Zg==");
        assert_eq!(base64(b"fo"), "Zm8=");
        assert_eq!(base64(b"foo"), "Zm9v");
        assert_eq!(base64(b"foobar"), "Zm9vYmFy");
    }

    #[test]
    fn cargo_包名从_package_段取() {
        let dir = tempfile::tempdir().unwrap();
        let path = dir.path().join("Cargo.toml");
        std::fs::write(&path, "[dependencies]\nname = \"wrong\"\n\n[package]\nname = \"athena-snake\"\nversion = \"1\"\n").unwrap();
        assert_eq!(cargo_package_name(&path).as_deref(), Some("athena-snake"));
    }

    #[test]
    fn 迷你仓库生成清单() {
        let dir = tempfile::tempdir().unwrap();
        let repo = dir.path();
        let app_dir = repo.join("programming/snake");
        std::fs::create_dir_all(app_dir.join("src-tauri")).unwrap();
        std::fs::create_dir_all(repo.join("scripts")).unwrap();
        std::fs::write(
            repo.join("scripts/release_apps.json"),
            r#"[{"id":"snake","root":"programming","kind":"tauri"},{"id":"launcher","root":"launcher","dir":"launcher/webui","kind":"tauri"},{"id":"driver","root":"certification","kind":"driver"}]"#,
        )
        .unwrap();
        std::fs::write(app_dir.join("app.json"), r##"{"id":"snake","title":"贪吃蛇","description":"x","group":"程序设计","icon":{"letter":"蛇"}}"##).unwrap();
        std::fs::write(
            app_dir.join("src-tauri/tauri.conf.json"),
            r#"{"productName":"贪吃蛇","identifier":"cn.athena.snake","mainBinaryName":"athena-snake"}"#,
        )
        .unwrap();
        let entries = generate(repo).unwrap();
        assert_eq!(entries.len(), 1, "launcher 与没有 app.json 的条目跳过");
        let snake = &entries[0];
        assert_eq!(snake.product_name.as_deref(), Some("贪吃蛇"));
        assert_eq!(snake.main_binary.as_deref(), Some("athena-snake"));
        assert_eq!(snake.identifier.as_deref(), Some("cn.athena.snake"));
        assert_eq!(snake.kind, "tauri");
        let json = to_json(&entries);
        assert!(json.ends_with("}\n]\n") || json.ends_with("]\n"));
        let back: Vec<CatalogEntry> = serde_json::from_str(&json).unwrap();
        assert_eq!(back, entries, "往返不丢字段");
    }

    #[test]
    fn 条目转_app_按安装位置设目录() {
        let entry = CatalogEntry {
            id: "snake".into(),
            title: "贪吃蛇".into(),
            summary: String::new(),
            symbol: "book".into(),
            letter: "蛇".into(),
            accent: "#000000".into(),
            group: None,
            related: vec![],
            evolves_from: None,
            parent: None,
            also_under: vec![],
            also_in: vec![],
            hidden: false,
            lifecycle: "built".into(),
            kind: "tauri".into(),
            product_name: Some("贪吃蛇".into()),
            main_binary: Some("athena-snake".into()),
            identifier: None,
            progress: None,
            icon: Some("data:image/svg+xml;base64,AA==".into()),
        };
        let installed = into_apps(vec![entry.clone()], |_| Some(PathBuf::from("/opt/snake/athena-snake")));
        assert_eq!(installed[0].dir, PathBuf::from("/opt/snake"));
        assert!(installed[0].install.as_ref().unwrap().installed);
        assert_eq!(installed[0].lifecycle, Lifecycle::Built);
        assert_eq!(installed[0].dev.binary.as_deref(), Some("athena-snake"));
        assert!(installed[0].embedded_icon.is_some());

        let missing = into_apps(vec![entry.clone()], |_| None);
        let install = missing[0].install.as_ref().unwrap();
        assert!(!install.installed && install.supported);
        assert!(missing[0].dir.is_relative(), "没装的应用 dir 不能是真路径");

        let mut driver = entry;
        driver.kind = "driver".into();
        let unsupported = into_apps(vec![driver], |_| Some(PathBuf::from("/never/asked")));
        let install = unsupported[0].install.as_ref().unwrap();
        assert!(!install.supported && !install.installed && install.exe.is_none(), "异构应用不去找安装位置");
    }

    /// 应用清单变了而没重新生成 catalog.json，这里红。修法：`launcher catalog`。
    #[test]
    fn catalog_is_up_to_date() {
        check(&repo_root()).unwrap();
    }

    #[test]
    fn 内嵌清单能解析且含已发布应用() {
        let entries = load_embedded();
        assert!(entries.iter().any(|e| e.id == "snake"), "内嵌清单里应有贪吃蛇");
        assert!(entries.iter().all(|e| !e.title.is_empty()));
    }
}
