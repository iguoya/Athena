//! 应用清单：`apps/<id>/app.json`。
//!
//! 每个应用只**声明**自己怎么构建、怎么跑、怎么算就绪；执行统一由编排器负责。
//! 这样各应用不必各写一份形状相同的 dev 脚本，改一次行为也不用改五遍。

use std::collections::BTreeMap;
use std::path::{Path, PathBuf};

use serde::Deserialize;

/// 环境变量的值。除了直接给字符串，还可以让编排器从几个候选里挑第一个存在的
/// 路径——`apps/c` 找 Qt 前缀就是这么干的，各平台装在哪不一样。
#[derive(Debug, Clone, Deserialize)]
#[serde(untagged)]
pub enum EnvValue {
    Literal(String),
    FirstExisting {
        first_existing: Vec<String>,
    },
}

impl EnvValue {
    /// `${dir}` 展开成应用目录的绝对路径；候选路径取第一个真实存在的。
    pub fn resolve(&self, dir: &Path) -> Option<String> {
        match self {
            EnvValue::Literal(text) => {
                Some(text.replace("${dir}", &dir.to_string_lossy()))
            }
            EnvValue::FirstExisting { first_existing } => first_existing
                .iter()
                .map(|candidate| candidate.replace("${dir}", &dir.to_string_lossy()))
                .find(|candidate| Path::new(candidate).exists()),
        }
    }
}

/// 启动前要做的一步准备：装依赖、配置构建、增量编译。
#[derive(Debug, Clone, Deserialize)]
pub struct PrepareStep {
    /// 只有这个路径不存在时才执行（相对应用目录）。用于 `npm install`、`meson setup`
    /// 这种一次性步骤；不写就每次都跑，增量构建属于这一类。
    #[serde(default)]
    pub when_missing: Option<String>,
    pub run: Vec<String>,
    /// 给人看的一句话，界面上显示"正在做什么"。
    #[serde(default)]
    pub label: Option<String>,
}

/// 怎么算"这个应用已经起来了"。
#[derive(Debug, Clone, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ReadySpec {
    /// 能连上这个地址就算就绪——Tauri 应用的 dev server。
    Http(String),
    /// 没有服务端口的应用（Qt、GTK）：进程在就算就绪。
    Process,
}

impl Default for ReadySpec {
    fn default() -> Self {
        ReadySpec::Process
    }
}

#[derive(Debug, Clone, Default, Deserialize)]
pub struct DevSpec {
    #[serde(default)]
    pub env: BTreeMap<String, EnvValue>,
    #[serde(default)]
    pub prepare: Vec<PrepareStep>,
    /// 真正长驻的那条命令，相对应用目录执行。
    #[serde(default)]
    pub run: Vec<String>,
    #[serde(default)]
    pub ready: ReadySpec,
    /// 判断进程属于本应用时用的路径前缀（相对应用目录）。默认就是应用目录本身；
    /// `apps/cpp` 的窗口进程落在 `builddir/` 里，仓库里别的进程不该被算进来。
    #[serde(default)]
    pub r#match: Option<String>,
    /// 窗口进程的可执行文件名。共享 cargo 缓存之后，Tauri 应用的二进制落在
    /// 仓库的 `.cache/cargo-target/` 下，已经不在应用目录里了，光靠路径前缀
    /// 认不出来——按文件名认最直接。
    #[serde(default)]
    pub binary: Option<String>,
}

#[derive(Debug, Clone, Deserialize)]
struct IconSpec {
    /// macOS 菜单栏版用的 SF Symbol 名。
    #[serde(default)]
    symbol: Option<String>,
    /// 图块里的字，通常一到三个字符（"C++"、"算"）。
    #[serde(default)]
    letter: Option<String>,
    /// 图块底色，取各自技术生态的惯用色，不自造。
    #[serde(default)]
    accent: Option<String>,
    /// 图块里的图标，相对应用目录的 SVG。图标跟着应用走，启动器不认识谁是谁。
    #[serde(default)]
    file: Option<String>,
}

#[derive(Debug, Clone, Deserialize)]
struct RawManifest {
    id: String,
    title: String,
    #[serde(default)]
    description: String,
    #[serde(default)]
    icon: Option<IconSpec>,
    #[serde(default)]
    dev: Option<DevSpec>,
    #[serde(default)]
    evolves_from: Option<String>,
}

#[derive(Debug, Clone)]
pub struct App {
    pub id: String,
    pub title: String,
    pub summary: String,
    pub symbol: String,
    pub letter: String,
    pub accent: String,
    /// 没有图标文件时退回 `letter`。
    pub icon_file: Option<PathBuf>,
    pub dir: PathBuf,
    pub dev: DevSpec,
    /// 这个学科是从哪个学科长出来的（C++ 之于 C）。只记真实的历史演进关系；
    /// 各自独立的知识体系就空着，不为了连线而连线。
    pub evolves_from: Option<String>,
}

impl App {
    /// 判断进程归属用的绝对路径前缀。
    pub fn match_prefix(&self) -> PathBuf {
        match &self.dev.r#match {
            Some(relative) => self.dir.join(relative),
            None => self.dir.clone(),
        }
    }

    /// 没有 `run` 就说明这个应用还没接入编排器，只能提示怎么手动启动。
    pub fn is_runnable(&self) -> bool {
        !self.dev.run.is_empty()
    }
}

/// 扫描 `<repo>/apps/*/app.json`。顺序按目录名排，界面上的次序才不随文件系统变。
/// 这里没有任何针对某个应用的分支：C++ 教程也只是 `apps/cpp`（ADR 0045）。
pub fn discover(repo: &Path) -> Vec<App> {
    discover_in(&repo.join("apps"))
}

/// `discover` 的通用版本：扫描任意一层 `<root>/*/app.json`，不写死 `apps/`。
/// `apps/practice/` 下将来会挂多个独立小项目，`practice` 面板复用同一套发现
/// 逻辑，只是换一个根目录（不用为它另写一份）。
pub fn discover_in(apps_root: &Path) -> Vec<App> {
    let mut entries: Vec<PathBuf> = match std::fs::read_dir(apps_root) {
        Ok(reader) => reader
            .filter_map(Result::ok)
            .map(|entry| entry.path())
            .filter(|path| path.is_dir())
            .collect(),
        Err(_) => return Vec::new(),
    };
    entries.sort();

    entries.iter().filter_map(|dir| parse(dir)).collect()
}

fn parse(dir: &Path) -> Option<App> {
    let text = std::fs::read_to_string(dir.join("app.json")).ok()?;
    let raw: RawManifest = match serde_json::from_str(&text) {
        Ok(value) => value,
        Err(error) => {
            eprintln!("{} 的 app.json 读不动：{error}", dir.display());
            return None;
        }
    };
    let icon = raw.icon.clone();
    Some(App {
        // 没写 letter 就取标题第一个字：新增应用不配这两项也能显示。
        letter: icon
            .as_ref()
            .and_then(|icon| icon.letter.clone())
            .unwrap_or_else(|| raw.title.chars().take(1).collect()),
        accent: icon
            .as_ref()
            .and_then(|icon| icon.accent.clone())
            .unwrap_or_else(|| "#5A6270".to_string()),
        icon_file: icon
            .as_ref()
            .and_then(|icon| icon.file.clone())
            .map(|name| dir.join(name))
            .filter(|path| path.is_file()),
        id: raw.id,
        title: raw.title,
        summary: raw.description,
        symbol: raw
            .icon
            .and_then(|icon| icon.symbol)
            .unwrap_or_else(|| "book".to_string()),
        dir: dir.to_path_buf(),
        dev: raw.dev.unwrap_or_default(),
        evolves_from: raw.evolves_from,
    })
}
