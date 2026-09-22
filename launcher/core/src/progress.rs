//! `launcher sync`：把进度库提交并推送（ADR 0053）。
//!
//! 进度库跟着仓库走，所以"同步"就是一次 git 提交加一次推送。这条命令存在的
//! 理由只有一个：**不连带使用者手上的代码改动**。顺手敲 `git commit -a` 很容易
//! 把半成品一起发出去，而 `git commit -- <路径>` 只提交指定路径，索引里别的
//! 东西保持原样。
//!
//! 推送这一步不能只发某几个提交——push 是分支级的。所以这里的规矩是：待推送
//! 的提交全是进度提交才自动推，否则把别的提交列出来交回使用者，不替他决定。

use std::path::Path;
use std::process::Command;

use crate::manifest::App;

/// textconv 让 `git diff` 能看见进度库里到底哪条记录变了，而不是一句
/// "Binary files differ"。它是本机配置（`.git/config`），不随仓库走，所以每台
/// 机器都得配一次——配在这里而不是写进文档让人照着敲，少一处会忘的地方。
const TEXTCONV_KEY: &str = "diff.sqlite.textconv";
const TEXTCONV_COMMAND: &str = "python3 scripts/db-textconv.py";

const COMMIT_PREFIX: &str = "progress:";

pub fn sync(repo: &Path, apps: &[App], mut report: impl FnMut(&str)) -> Result<(), String> {
    let paths = progress_paths(repo, apps);
    if paths.is_empty() {
        report("还没有任何进度库——先打开应用做几道题，再回来同步。");
        return Ok(());
    }

    ensure_textconv(repo, &mut report)?;

    // 首次同步时库还是未跟踪的，而 `git commit -- <路径>` 带不上未跟踪文件，
    // 所以先 add 一次。
    run(repo, &join(&["add", "--"], &paths))?;

    if succeeded(repo, &join(&["diff", "--cached", "--quiet", "--"], &paths))? {
        report("进度没有变化，不用提交。");
    } else {
        run(
            repo,
            &join(
                &["commit", "-m", "progress: 同步学习进度", "--"],
                &paths,
            ),
        )?;
        report("已提交进度变更。");
    }

    push(repo, &mut report)
}

fn push(repo: &Path, report: &mut impl FnMut(&str)) -> Result<(), String> {
    let Some(upstream) = output(repo, &["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"])
    else {
        report(
            "当前分支没有上游，进度只提交在本地。\n\
             设好上游（git push -u origin <分支>）之后再同步就会自动推送。",
        );
        return Ok(());
    };

    let Some(pending) = output(repo, &["log", "--format=%s", &format!("{upstream}..HEAD")]) else {
        report("远端已经是最新的。");
        return Ok(());
    };

    let others: Vec<&str> = pending
        .lines()
        .filter(|subject| !subject.starts_with(COMMIT_PREFIX))
        .collect();
    if !others.is_empty() {
        // 只列头几条：待推送的代码提交攒到几十个很常见，全铺出来反而看不清。
        const SHOWN: usize = 5;
        let mut listed: Vec<String> = others.iter().take(SHOWN).map(|s| format!("  {s}")).collect();
        if others.len() > SHOWN {
            listed.push(format!("  …… 另有 {} 个", others.len() - SHOWN));
        }
        report(&format!(
            "进度已提交在本地，但没有推送：待推送的 {} 个提交里有 {} 个不是进度提交，\n\
             而 push 是整条分支一起发的，这条命令不替你决定发不发你的代码：\n{}\n\
             确认没问题就自己执行 git push。",
            pending.lines().count(),
            others.len(),
            listed.join("\n")
        ));
        return Ok(());
    }

    run(repo, &["push"]).map_err(|message| {
        format!("{message}\n远端有新提交时，先 git pull --rebase 再同步。")
    })?;
    report(&format!("已推送到 {upstream}。"));
    Ok(())
}

/// 每个应用自己目录下的 `progress/`，转成相对仓库根的 pathspec。
///
/// 按 `app.dir` 推而不是拼 `apps/<id>`：id 来自 `app.json`，跟目录名不保证
/// 一样（`mathematics` 的知识点前缀就是 `math.`，两者有意不同）。
fn progress_paths(repo: &Path, apps: &[App]) -> Vec<String> {
    apps.iter()
        .filter_map(|app| {
            let directory = app.dir.join("progress");
            if !directory.is_dir() {
                return None;
            }
            let relative = directory.strip_prefix(repo).ok()?;
            // pathspec 在三个平台上都用正斜杠。
            Some(relative.to_string_lossy().replace('\\', "/"))
        })
        .collect()
}

fn ensure_textconv(repo: &Path, report: &mut impl FnMut(&str)) -> Result<(), String> {
    if output(repo, &["config", "--local", "--get", TEXTCONV_KEY]).as_deref()
        == Some(TEXTCONV_COMMAND)
    {
        return Ok(());
    }
    run(repo, &["config", "--local", TEXTCONV_KEY, TEXTCONV_COMMAND])?;
    report("已配好 git 的 sqlite textconv：git diff 现在能看见进度库的内容。");
    Ok(())
}

fn join<'a>(head: &[&'a str], tail: &'a [String]) -> Vec<&'a str> {
    let mut all: Vec<&str> = head.to_vec();
    all.extend(tail.iter().map(String::as_str));
    all
}

fn git(repo: &Path, arguments: &[&str]) -> Result<(bool, String), String> {
    let result = Command::new("git")
        .current_dir(repo)
        .args(arguments)
        .output()
        .map_err(|error| format!("git {} 没能执行：{error}", arguments.join(" ")))?;
    let mut text = String::from_utf8_lossy(&result.stdout).into_owned();
    text.push_str(&String::from_utf8_lossy(&result.stderr));
    Ok((result.status.success(), text.trim().to_string()))
}

/// 只关心成功与否的调用（`diff --quiet` 用退出码表达"有没有差异"）。
fn succeeded(repo: &Path, arguments: &[&str]) -> Result<bool, String> {
    Ok(git(repo, arguments)?.0)
}

/// 失败就把 git 自己的话原样带出来——我们没有比它更准确的说法。
fn run(repo: &Path, arguments: &[&str]) -> Result<(), String> {
    let (ok, message) = git(repo, arguments)?;
    if ok {
        return Ok(());
    }
    Err(format!("git {} 失败：{message}", arguments.join(" ")))
}

/// 成功且有输出时给出内容，其余情况一律 None（分支没上游、没有待推送提交
/// 这两种都是正常状态，不是错误）。
fn output(repo: &Path, arguments: &[&str]) -> Option<String> {
    let (ok, text) = git(repo, arguments).ok()?;
    if ok && !text.is_empty() {
        Some(text)
    } else {
        None
    }
}
