//! 应用清单：`subjects/<id>/app.json`。
//!
//! 每个应用只**声明**自己怎么构建、怎么跑、怎么算就绪；执行统一由编排器负责。
//! 这样各应用不必各写一份形状相同的 dev 脚本，改一次行为也不用改五遍。

use std::collections::BTreeMap;
use std::path::{Path, PathBuf};

use serde::Deserialize;

/// 环境变量的值。除了直接给字符串，还可以让编排器从几个候选里挑第一个存在的
/// 路径——`subjects/machine` 找 Qt 前缀就是这么干的，各平台装在哪不一样。
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
    /// `subjects/cpp` 的窗口进程落在 `builddir/` 里，仓库里别的进程不该被算进来。
    #[serde(default)]
    pub r#match: Option<String>,
    /// 窗口进程的可执行文件名。同类 Tauri 共享 `.cache/cargo-target/` 后（ADR 0063），
    /// 二进制不在应用目录的 `src-tauri/target` 下，光靠路径前缀认不出来——按文件名
    /// 认最直接。异构应用（产物仍在自己的 `build/` 里）主要靠 `match` 路径。
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
    /// 没有 `file` 时兜底色块的底色（ADR 0065 之后 `icon.svg` 自带颜色，不再垫它）。
    #[serde(default)]
    accent: Option<String>,
    /// 应用的图标，相对应用目录的彩色 SVG。图标跟着应用走，启动器不认识谁是谁；
    /// 启动器图块、窗口 / 任务栏、应用界面三处都从它来（ADR 0065）。
    #[serde(default)]
    file: Option<String>,
    /// `launcher icons` 要从 `file` 派生的位图：相对应用目录的路径 → 边长，
    /// 或 `"ico"` / `"icns"`。平台图标位只认位图，由这里一次渲染好提交进库。
    #[serde(default)]
    renders: BTreeMap<String, RawRender>,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(untagged)]
enum RawRender {
    Size(u32),
    Format(String),
}

/// 一份派生位图的格式。
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum RenderSpec {
    /// 边长为 n 的 PNG。
    Png(u32),
    /// 多尺寸 `.ico`（Windows exe 资源、Tauri / Flutter 的 Windows 图标位）。
    Ico,
    /// 多尺寸 `.icns`（macOS）。
    Icns,
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
    #[serde(default)]
    group: Option<String>,
    #[serde(default)]
    related: Vec<String>,
    /// 挂靠的应用 id：本应用是它底下的子课程/子能力（ADR 0092）。有向、单父；
    /// 布局时画在挂靠者外一圈。找不到的 id 布局时忽略。
    #[serde(default)]
    parent: Option<String>,
    /// 显示层隐藏（ADR 0093）：不出现在任何面板，`list --json` 仍返回并带标记；
    /// open/stop 与 dev 编排照常可用——隐藏是显示层的事，不是下线。
    #[serde(default)]
    hidden: bool,
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
    /// `icon.renders`：相对应用目录的路径与格式，按路径排序。
    pub icon_renders: Vec<(String, RenderSpec)>,
    pub dir: PathBuf,
    pub dev: DevSpec,
    /// 这个学科是从哪个学科长出来的（C++ 之于 C）。只记真实的历史演进关系；
    /// 各自独立的知识体系就空着，不为了连线而连线。
    pub evolves_from: Option<String>,
    /// 领域分组（思维导图里同组的应用挂在同一个分支上）；省略归「其他」（ADR 0083）。
    pub group: Option<String>,
    /// 相关应用的 id。无向：只在一边声明就行；找不到的 id 布局时忽略（ADR 0083）。
    pub related: Vec<String>,
    /// 挂靠的应用 id：本应用是它底下的子课程/子能力（ADR 0092）。有向、单父。
    pub parent: Option<String>,
    /// 显示层隐藏（ADR 0093）：不进任何面板，清单与编排仍可见。
    pub hidden: bool,
}

impl App {
    /// 判断进程归属用的绝对路径前缀。
    pub fn match_prefix(&self) -> PathBuf {
        match &self.dev.r#match {
            Some(relative) => self.dir.join(relative),
            None => self.dir.clone(),
        }
    }

    /// `icon.renders` 里最大的一张 PNG（已存在才算）。给只吃位图的前端用。
    pub fn largest_png(&self) -> Option<PathBuf> {
        self.icon_renders
            .iter()
            .filter_map(|(path, spec)| match spec {
                RenderSpec::Png(size) => Some((*size, self.dir.join(path))),
                _ => None,
            })
            .filter(|(_, path)| path.is_file())
            .max_by_key(|(size, _)| *size)
            .map(|(_, path)| path)
    }

    /// 没有 `run` 就说明这个应用还没接入编排器，只能提示怎么手动启动。
    pub fn is_runnable(&self) -> bool {
        !self.dev.run.is_empty()
    }
}

/// 扫描 `<repo>/subjects/*/app.json`。顺序按目录名排，界面上的次序才不随文件系统变。
/// 这里没有任何针对某个应用的分支：C++ 教程也只是 `subjects/cpp`（ADR 0045）。
pub fn discover(repo: &Path) -> Vec<App> {
    discover_in(&repo.join("subjects"))
}

/// `discover` 的通用版本：扫描任意一层 `<root>/*/app.json`，不写死 `subjects/`。
/// `practice/` 下将来会挂多个独立小项目，`practice` 面板复用同一套发现
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
    let mut icon_renders = Vec::new();
    for (path, spec) in icon.as_ref().map(|icon| &icon.renders).into_iter().flatten() {
        let spec = match spec {
            RawRender::Size(size) if *size > 0 => RenderSpec::Png(*size),
            RawRender::Format(format) if format == "ico" => RenderSpec::Ico,
            RawRender::Format(format) if format == "icns" => RenderSpec::Icns,
            _ => {
                // 跟 accent 写错一样：不让启动器起不来，但要点名是谁、哪一项。
                eprintln!("{} 的 icon.renders「{path}」：只认正整数边长、\"ico\"、\"icns\"，已跳过", dir.display());
                continue;
            }
        };
        icon_renders.push((path.clone(), spec));
    }
    Some(App {
        icon_renders,
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
        group: raw.group,
        related: raw.related,
        parent: raw.parent,
        hidden: raw.hidden,
    })
}

/// 一份清单的指纹：前后两次扫描的指纹相同，就说明清单没变。
///
/// 常驻的启动器靠文件通知感知变更（ADR 0001），通知来了要重扫清单；重扫本身
/// 便宜（一次 `read_dir` 加二十来个小文件），贵的是跟着重建——图标重渲染、
/// 思维导图重排、托盘菜单整条换掉。所以重扫之后先比指纹，没变就不动界面。
///
/// 指纹只在进程内部前后比较，`{:?}` 的展开在同一进程里是稳定的，`App` 以后
/// 加字段会自动跟着进指纹；图标文件另拼上修改时间与长度——只改 `icon.svg`
/// 不动 `app.json`，界面也要跟得上。
pub fn fingerprint(apps: &[App]) -> String {
    let mut out = format!("{apps:?}\n");
    for app in apps {
        let Some(icon) = &app.icon_file else { continue };
        match std::fs::metadata(icon) {
            Ok(meta) => {
                out += &format!("icon {}\n{:?}\n{}\n", icon.display(), meta.modified(), meta.len());
            }
            Err(error) => out += &format!("icon {} 失联：{error}\n", icon.display()),
        }
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::path::PathBuf;

    fn app(id: &str, title: &str) -> App {
        App {
            id: id.to_string(),
            title: title.to_string(),
            summary: String::new(),
            symbol: "book".to_string(),
            letter: "A".to_string(),
            accent: "#5A6270".to_string(),
            icon_file: None,
            icon_renders: Vec::new(),
            dir: PathBuf::new(),
            dev: DevSpec::default(),
            evolves_from: None,
            group: None,
            related: Vec::new(),
            parent: None,
            hidden: false,
        }
    }

    /// 同一份清单扫两遍，指纹必须一致——否则常驻期间每次重扫都会白白重建界面。
    #[test]
    fn 同一清单指纹稳定() {
        let apps = vec![app("a", "甲"), app("b", "乙")];
        assert_eq!(fingerprint(&apps), fingerprint(&apps));
    }

    #[test]
    fn 改标题指纹要变() {
        assert_ne!(fingerprint(&[app("a", "甲")]), fingerprint(&[app("a", "乙")]));
    }

    #[test]
    fn 增删应用指纹要变() {
        let base = vec![app("a", "甲"), app("b", "乙")];
        assert_ne!(fingerprint(&base), fingerprint(&[app("a", "甲")]));
        assert_ne!(fingerprint(&base), fingerprint(&[app("a", "甲"), app("b", "乙"), app("c", "丙")]));
    }

    /// 只改图标文件不动 app.json 也要能看出来：指纹里拼了修改时间与长度。
    #[test]
    fn 图标文件变了指纹要变() {
        struct TempIcon(std::path::PathBuf);
        impl Drop for TempIcon {
            fn drop(&mut self) {
                let _ = std::fs::remove_file(&self.0);
            }
        }
        let path = std::env::temp_dir().join("athena-launcher-fingerprint-test.svg");
        std::fs::write(&path, "<svg/>").expect("写临时图标");
        let _guard = TempIcon(path.clone());

        let mut application = app("a", "甲");
        application.icon_file = Some(path.clone());
        let before = fingerprint(&[application.clone()]);
        std::fs::write(&path, "<svg width=\"2\"/>").expect("改临时图标");
        assert_ne!(before, fingerprint(&[application]));
    }
}
