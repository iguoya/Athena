//! 朗读：调系统 TTS，不走 WebView 的 Web Speech（ADR 0026）。
//!
//! 起因是实测发现 WKWebView 只暴露 Meijia 和 Tingting 两个中文语音，使用者下载
//! 的 Premium 语音、乃至系统自带的 Shelley/Sandy/Flo 全都看不见；而同一台机器上
//! `say -v '?'` 有 21 个。这不是配置问题，Web Speech 在那边就是只挂着一小撮内置
//! 语音，所以只能绕过它。
//!
//! 与 `engine.rs` 是同一套做法——Rust 侧管一个不做业务的进程。区别是符号引擎必须
//! 常驻（`import sympy` 太贵），而 `say` 启动很轻，每句一个进程就够。

use serde::Serialize;
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;

#[derive(Serialize, Clone)]
pub struct NativeVoice {
    pub name: String,
    pub lang: String,
    /// 系统下载的增强版。`say -v '?'` 里以 "(Premium)" / "(Enhanced)" 标出
    pub better: bool,
}

#[derive(Default)]
pub struct Tts {
    /// 同一时刻只留一个朗读进程。新的一句先杀掉上一句，对应 Web Speech 的 cancel()
    speaking: Option<Child>,
}

impl Tts {
    pub fn stop(&mut self) {
        if let Some(mut c) = self.speaking.take() {
            let _ = c.kill();
            let _ = c.wait();
        }
    }

    /// 起一句。立刻返回，真正念完由 `wait_done` 等——不然朗读会阻塞整个命令线程。
    pub fn speak(&mut self, text: &str, voice: &str, rate: f64) -> Result<(), String> {
        self.stop();
        if text.trim().is_empty() {
            return Ok(());
        }
        let mut cmd = Command::new("say");
        if !voice.is_empty() {
            cmd.arg("-v").arg(voice);
        }
        // Web Speech 的 rate 是倍数，say 的 -r 是每分钟词数（默认约 175）。
        // 这个系数是估的：中文按字计与英文按词计不同，要实际听过再调（ADR 0026 第 3 节）。
        let wpm = (175.0 * rate).clamp(90.0, 500.0).round() as i32;
        cmd.arg("-r").arg(wpm.to_string());
        cmd.arg("--").arg(text);
        let child = cmd
            .stdin(Stdio::null())
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .spawn()
            .map_err(|e| format!("启动 say 失败：{e}"))?;
        self.speaking = Some(child);
        Ok(())
    }

    /// 当前这句念完了没有。前端轮询它来串起「一段念完再念下一段」。
    pub fn finished(&mut self) -> bool {
        match self.speaking.as_mut() {
            None => true,
            Some(c) => match c.try_wait() {
                Ok(Some(_)) => {
                    self.speaking = None;
                    true
                }
                Ok(None) => false,
                // 等不动了就当它结束，否则朗读会卡在这一句上再也走不下去
                Err(_) => {
                    self.speaking = None;
                    true
                }
            },
        }
    }
}

/// 解析 `say -v '?'`。每行形如：
/// `Lilian (Premium)    zh_CN    # 你好！我叫黎潋。`
/// 名字里可能有空格，所以按「两个以上空格」切，而不是按单个空格。
pub fn list_native_voices() -> Vec<NativeVoice> {
    let out = match Command::new("say").arg("-v").arg("?").output() {
        Ok(o) => o,
        Err(_) => return Vec::new(),
    };
    let text = String::from_utf8_lossy(&out.stdout);
    let mut voices = Vec::new();
    for line in text.lines() {
        let head = line.split('#').next().unwrap_or("");
        let mut parts = head.split("  ").filter(|s| !s.trim().is_empty());
        let (Some(name), Some(lang)) = (parts.next(), parts.next()) else {
            continue;
        };
        let name = name.trim().to_string();
        let lang = lang.trim().replace('_', "-");
        if !lang.to_lowercase().starts_with("zh") {
            continue;
        }
        let better = name.contains("(Premium)") || name.contains("(Enhanced)");
        voices.push(NativeVoice { name, lang, better });
    }
    voices
}

pub type TtsState = Mutex<Tts>;
