//! `athena-dev`：终端里的编排器入口，也是 GUI 之外的备用路径。
//!
//! 用法：
//!   athena-dev list             列出全部应用和当前状态
//!   athena-dev list --json      同上，机器读的格式；菜单栏版靠它认应用（ADR 0048）
//!   athena-dev open <id>        打开：已在跑就把窗口叫到前面，没跑才构建并启动
//!   athena-dev stop <id>        停止它，连同构建期拉起的那一串
//!   athena-dev logs <id>        打印日志文件路径

use std::process::ExitCode;

use athena_dev::{discover, paths, runner, App, ProcessSnapshot};

/// 管道被下游关掉（`athena-dev list | head`）时不该炸成 panic，安静收工就好。
fn line(text: &str) {
    use std::io::Write;
    let _ = writeln!(std::io::stdout(), "{text}");
}

fn main() -> ExitCode {
    let arguments: Vec<String> = std::env::args().skip(1).collect();
    let Some(repo) = paths::locate_repo() else {
        eprintln!("找不到 Athena 仓库：设置 ATHENA_ROOT，或在仓库里执行。");
        return ExitCode::FAILURE;
    };
    let apps = discover(&repo);

    match arguments.first().map(String::as_str) {
        None | Some("list") => {
            let snapshot = ProcessSnapshot::take();
            if arguments.get(1).map(String::as_str) == Some("--json") {
                line(&listing_json(&apps, &snapshot));
                return ExitCode::SUCCESS;
            }
            for app in &apps {
                let state = snapshot.state(app);
                let note = if app.is_runnable() {
                    String::new()
                } else {
                    "  （app.json 里还没有 dev.run）".to_string()
                };
                line(&format!("{}\t{}\t{}{}", app.id, app.title, state.label(), note));
            }
            ExitCode::SUCCESS
        }
        Some("open") => match pick(&apps, arguments.get(1)) {
            Ok(app) => open(app, &repo),
            Err(code) => code,
        },
        Some("stop") => match pick(&apps, arguments.get(1)) {
            Ok(app) => match runner::stop(app) {
                Ok(()) => {
                    line(&format!("已停止 {}", app.title));
                    ExitCode::SUCCESS
                }
                Err(message) => {
                    eprintln!("{message}");
                    ExitCode::FAILURE
                }
            },
            Err(code) => code,
        },
        Some("logs") => match pick(&apps, arguments.get(1)) {
            Ok(app) => {
                line(&paths::log_file(&app.id).display().to_string());
                ExitCode::SUCCESS
            }
            Err(code) => code,
        },
        Some(other) => {
            eprintln!("不认识的命令：{other}");
            ExitCode::FAILURE
        }
    }
}

/// 清单 + 状态的机器可读版本。
///
/// 菜单栏版原来自己再解析一遍 app.json，字段默认值在 Rust 和 Swift 各写一份，
/// 已经开始对不上（symbol 的兜底一边是 "book" 一边是 "book.closed"）。清单怎么
/// 读只保留这一处，前端消费结论就行（ADR 0046、0048）。
fn listing_json(apps: &[App], snapshot: &ProcessSnapshot) -> String {
    let rows: Vec<serde_json::Value> = apps
        .iter()
        .map(|app| {
            serde_json::json!({
                "id": app.id,
                "title": app.title,
                "summary": app.summary,
                "symbol": app.symbol,
                "dir": app.dir,
                "matchPrefix": app.match_prefix(),
                "binary": app.dev.binary.clone().unwrap_or_default(),
                "runnable": app.is_runnable(),
                "state": snapshot.state(app).key(),
                "log": paths::log_file(&app.id),
            })
        })
        .collect();
    serde_json::to_string_pretty(&rows).unwrap_or_else(|_| "[]".to_string())
}

fn pick<'a>(apps: &'a [App], wanted: Option<&String>) -> Result<&'a App, ExitCode> {
    let Some(wanted) = wanted else {
        eprintln!("要指定应用 id，例如 athena-dev open dsa");
        return Err(ExitCode::FAILURE);
    };
    apps.iter().find(|app| &app.id == wanted).ok_or_else(|| {
        eprintln!("没有这个应用：{wanted}");
        ExitCode::FAILURE
    })
}

fn open(app: &App, repo: &std::path::Path) -> ExitCode {
    // 已经在跑就只把窗口叫到前面——绝不起第二份。
    let snapshot = ProcessSnapshot::take();
    if snapshot.state(app) != athena_dev::RunState::Stopped {
        return match runner::activate(app) {
            Ok(()) => ExitCode::SUCCESS,
            Err(message) => {
                line(&message);
                ExitCode::SUCCESS
            }
        };
    }

    match runner::launch(app, repo, line) {
        Ok(pid) => {
            line(&format!(
                "{} 已启动（pid {pid}），日志：{}",
                app.title,
                paths::log_file(&app.id).display()
            ));
            ExitCode::SUCCESS
        }
        Err(message) => {
            eprintln!("{message}");
            ExitCode::FAILURE
        }
    }
}
