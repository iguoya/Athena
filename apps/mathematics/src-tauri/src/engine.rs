//! 符号引擎的常驻子进程（ADR 0025）。
//!
//! Rust 侧**仍然不做数学**——ADR 0001 那条没变，只是职责从「什么都不做」变成
//! 「管一个不做数学的进程」：启动、重启、转发。表达式怎么解析、怎么判等全在
//! Python 侧，这里不看内容。
//!
//! 进程按需启动并常驻：`import sympy` 加预热将近一秒，实测占冷启动的九成以上，
//! 而判等本身只要几毫秒。这笔钱只付一次，是整个方案的全部理由。

use serde::Serialize;
use std::io::{BufRead, BufReader, Write};
use std::path::{Path, PathBuf};
use std::process::{Child, ChildStdin, ChildStdout, Command, Stdio};
use std::sync::Mutex;

/// 引擎说不清楚时给前端的统一形状。`verdict` 只有 equal / different / unknown
/// 三种，**unknown 不许在任何一层被折叠成 different**（ADR 0001 第 1 节第 3 条）。
#[derive(Serialize, Clone)]
pub struct EngineReply {
    pub ok: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub verdict: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub note: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub error: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub ms: Option<f64>,
}

impl EngineReply {
    fn failed(msg: impl Into<String>) -> Self {
        Self { ok: false, verdict: None, note: None, error: Some(msg.into()), ms: None }
    }
}

/// 引擎是否可用，以及为什么不可用。界面据此决定验算入口显不显示——
/// 不可用时要说清楚怎么修，而不是让人对着一个没反应的按钮（ADR 0011）。
#[derive(Serialize, Clone)]
pub struct EngineStatus {
    pub ready: bool,
    pub detail: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub sympy: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub import_ms: Option<f64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub warmup_ms: Option<f64>,
}

struct Running {
    child: Child,
    stdin: ChildStdin,
    stdout: BufReader<ChildStdout>,
    next_id: u64,
}

#[derive(Default)]
pub struct Engine {
    running: Option<Running>,
    /// 启动失败的原因。记下来是为了让界面能说清楚该跑哪个脚本，
    /// 而不是笼统地说「引擎不可用」。
    last_error: Option<String>,
}

/// venv 里解释器的位置：POSIX 是 `bin/python`，Windows 是 `Scripts\python.exe`。
/// 按存在与否挑，不按平台编译（ADR 0047）——两条都找不到时返回 POSIX 那条，
/// 让启动失败的报错里出现一个具体路径，好定位。
fn venv_python(app_root: &Path) -> PathBuf {
    let candidates = [
        app_root.join("engine/.venv/bin/python"),
        app_root.join("engine/.venv/Scripts/python.exe"),
    ];
    candidates
        .iter()
        .find(|path| path.is_file())
        .cloned()
        .unwrap_or_else(|| candidates[0].clone())
}

impl Engine {
    /// 启动并握手。失败时把原因留在 `last_error` 里，不 panic——
    /// 引擎起不来只该让验算功能不可用，不该让整个应用挂掉。
    fn start(&mut self, app_root: &Path) -> Result<(), String> {
        let py = venv_python(app_root);
        let script = app_root.join("engine/engine.py");

        if !py.is_file() {
            return Err(format!(
                "还没建引擎环境。跑一次 scripts/setup-engine.py 就好（缺 {}）",
                py.display()
            ));
        }
        if !script.is_file() {
            return Err(format!("找不到引擎脚本 {}", script.display()));
        }

        // -u：关掉 Python 的输出缓冲。少了它，回包会卡在管道里，表现成引擎「没反应」。
        //
        // PYTHONUTF8 / PYTHONIOENCODING：Windows 上 Python 的标准流默认跟随系统
        // 代码页（cp1252 / gbk），而 engine.py 回包用的是 `ensure_ascii=False`
        // ——一旦结果里带中文就会抛 UnicodeEncodeError 把引擎打死。这条链路此前
        // 只在 macOS 上跑过，所以一直没暴露（主仓库 ADR 0047）。
        let mut child = Command::new(&py)
            .arg("-u")
            .arg(&script)
            .env("PYTHONUTF8", "1")
            .env("PYTHONIOENCODING", "utf-8")
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::inherit())
            .spawn()
            .map_err(|e| format!("启动引擎失败：{e}"))?;

        let stdin = child.stdin.take().ok_or("拿不到引擎的 stdin")?;
        let stdout = BufReader::new(child.stdout.take().ok_or("拿不到引擎的 stdout")?);
        self.running = Some(Running { child, stdin, stdout, next_id: 1 });
        Ok(())
    }

    fn send(&mut self, req: serde_json::Value) -> Result<serde_json::Value, String> {
        let r = self.running.as_mut().ok_or("引擎没在运行")?;
        let line = serde_json::to_string(&req).map_err(|e| e.to_string())?;
        r.stdin
            .write_all(line.as_bytes())
            .and_then(|_| r.stdin.write_all(b"\n"))
            .and_then(|_| r.stdin.flush())
            .map_err(|e| format!("写给引擎失败：{e}"))?;

        let mut buf = String::new();
        let n = r.stdout.read_line(&mut buf).map_err(|e| format!("读引擎回包失败：{e}"))?;
        if n == 0 {
            return Err("引擎关闭了输出".into());
        }
        serde_json::from_str(&buf).map_err(|e| format!("引擎回包不是 JSON：{e}"))
    }

    /// 发一条请求；进程死了就重启一次再试。**只重试一次**——
    /// 反复重启会把一个确定的故障拖成一串看起来随机的超时。
    fn call(&mut self, app_root: &Path, op: &str, extra: serde_json::Value) -> Result<serde_json::Value, String> {
        for attempt in 0..2 {
            if self.running.is_none() {
                if let Err(e) = self.start(app_root) {
                    self.last_error = Some(e.clone());
                    return Err(e);
                }
            }
            let id = {
                let r = self.running.as_mut().unwrap();
                let id = r.next_id;
                r.next_id += 1;
                id
            };
            let mut req = serde_json::json!({ "id": id, "op": op });
            if let Some(obj) = extra.as_object() {
                for (k, v) in obj {
                    req[k] = v.clone();
                }
            }
            match self.send(req) {
                Ok(v) => return Ok(v),
                Err(e) => {
                    self.shutdown();
                    if attempt == 1 {
                        self.last_error = Some(e.clone());
                        return Err(e);
                    }
                }
            }
        }
        unreachable!()
    }

    fn shutdown(&mut self) {
        if let Some(mut r) = self.running.take() {
            drop(r.stdin);
            let _ = r.child.kill();
            let _ = r.child.wait();
        }
    }

    pub fn status(&mut self, app_root: &Path) -> EngineStatus {
        match self.call(app_root, "ping", serde_json::json!({})) {
            Ok(v) => EngineStatus {
                ready: v["ok"].as_bool().unwrap_or(false),
                detail: "就绪".into(),
                sympy: v["sympy"].as_str().map(str::to_string),
                import_ms: v["import_ms"].as_f64(),
                warmup_ms: v["warmup_ms"].as_f64(),
            },
            Err(e) => EngineStatus {
                ready: false,
                detail: e,
                sympy: None,
                import_ms: None,
                warmup_ms: None,
            },
        }
    }

    pub fn equiv(&mut self, app_root: &Path, a: &str, b: &str) -> EngineReply {
        match self.call(app_root, "equiv", serde_json::json!({ "a": a, "b": b })) {
            Ok(v) => EngineReply {
                ok: v["ok"].as_bool().unwrap_or(false),
                verdict: v["verdict"].as_str().map(str::to_string),
                note: v["note"].as_str().map(str::to_string),
                error: v["error"].as_str().map(str::to_string),
                ms: v["ms"].as_f64(),
            },
            Err(e) => EngineReply::failed(e),
        }
    }
}

pub type EngineState = Mutex<Engine>;

#[cfg(test)]
mod tests {
    use super::*;

    /// 这个测试同时验证两件事：Rust↔Python 那条管道通不通，以及
    /// **带未求值 ∫ 的判等到底能不能做**——后者正是 ADR 0025 选 SymPy 的全部理由，
    /// 随机数值代入在那种表达式上无能为力。
    #[test]
    fn round_trip_and_symbolic_integral() {
        let root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("..");
        let python = venv_python(&root);
        // 不跳过。这个测试验的是本应用最核心的那条链路，静默放过等于没测；
        // 环境按仓库基线视为可自行准备，缺了就说清楚怎么补（主仓库 AGENTS.md）。
        assert!(
            python.is_file(),
            "引擎环境还没建：先在 apps/mathematics 跑 python3 scripts/setup-engine.py（缺 {}）",
            python.display()
        );
        let mut e = Engine::default();

        let st = e.status(&root);
        assert!(st.ready, "引擎没起来：{}", st.detail);
        eprintln!(
            "sympy {} · import {:?} ms · warmup {:?} ms",
            st.sympy.clone().unwrap_or_default(),
            st.import_ms,
            st.warmup_ms
        );

        let cases = [
            ("x**2-1", "(x-1)*(x+1)", "equal"),
            ("(x+1)**2", "x**2+1", "different"),
            ("Integral(x*exp(x**2),x)", "exp(x**2)/2", "equal"),
            ("Limit(sin(x)/x,x,0)", "1", "equal"),
            // 只在 x≥0 时相等：判 unknown 是对的，判 equal 才是错的
            ("sqrt(x**2)", "x", "unknown"),
        ];
        for (a, b, want) in cases {
            let r = e.equiv(&root, a, b);
            assert!(r.ok, "{a} vs {b} 出错：{:?}", r.error);
            assert_eq!(r.verdict.as_deref(), Some(want), "{a} vs {b}");
            eprintln!("{a} ≟ {b} → {want} ({:?} ms)", r.ms);
        }

        // 进程死掉要能自己爬起来，而不是从此不可用
        e.shutdown();
        let again = e.equiv(&root, "x+x", "2*x");
        assert_eq!(again.verdict.as_deref(), Some("equal"), "重启后失效");

        e.shutdown();
    }
}
