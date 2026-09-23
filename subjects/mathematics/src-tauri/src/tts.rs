//! 朗读：调系统 TTS，不走 WebView 的 Web Speech（ADR 0026）。
//!
//! 起因是实测发现 WKWebView 只暴露 Meijia 和 Tingting 两个中文语音，使用者下载
//! 的 Premium 语音、乃至系统自带的 Shelley/Sandy/Flo 全都看不见；而同一台机器上
//! `say -v '?'` 有 21 个。后来查到 Windows 的 WebView2 有性质相同的毛病：
//! `speechSynthesis.getVoices()` 拿不到微软的 Natural voices，尽管 Edge 拿得到
//! （WebView2Feedback #2660）。两个平台撞的是同一堵墙——宿主 WebView 只暴露一小
//! 撮系统语音。
//!
//! 2026-09-15 改用 `tts` crate 这个通用方案，替掉原来直接调 macOS 的 `say`：
//! 它在 macOS 上走 AVFoundation、Windows 上走 WinRT `SpeechSynthesizer`
//! （拿得到 Natural voices）、Linux 上走 Speech Dispatcher。一套代码三个平台，
//! 不写平台分支，正是 ADR 0047 说的「优先选把平台差异自己吃掉的抽象」；顺带把
//! Linux 从「只能退回 Web Speech」提升到有原生朗读。

use serde::Serialize;
use std::sync::Mutex;

#[derive(Serialize, Clone)]
pub struct NativeVoice {
    /// 传回给 `speak` 用的标识。macOS 上是语音 id，不是显示名。
    pub name: String,
    pub lang: String,
    /// 系统下载的增强版，音质明显好过默认压缩版。各平台的标记词不同，
    /// 统一按名字里的关键词认。
    pub better: bool,
}

/// 名字里带这些词的算增强版：macOS 是 Premium / Enhanced，Windows 的高音质
/// 语音叫 Natural，Linux 各引擎叫法不一，能认多少算多少。
fn is_better(name: &str) -> bool {
    let lower = name.to_lowercase();
    ["premium", "enhanced", "natural", "neural"]
        .iter()
        .any(|k| lower.contains(k))
}

pub struct Tts {
    inner: Option<tts::Tts>,
}

impl Default for Tts {
    fn default() -> Self {
        // 系统没有可用的 TTS 后端时（例如 Linux 没装 speech-dispatcher）不 panic：
        // 朗读是锦上添花，前端拿到空语音表会自动退回 Web Speech。
        Self { inner: tts::Tts::default().ok() }
    }
}

impl Tts {
    pub fn stop(&mut self) {
        if let Some(t) = self.inner.as_mut() {
            let _ = t.stop();
        }
    }

    /// 起一句。立刻返回，真正念完由 `finished` 轮询——不然朗读会阻塞命令线程。
    pub fn speak(&mut self, text: &str, voice: &str, rate: f64) -> Result<(), String> {
        if text.trim().is_empty() {
            return Ok(());
        }
        let t = self.inner.as_mut().ok_or("这台机器上没有可用的系统语音后端")?;

        if !voice.is_empty() {
            let wanted = t
                .voices()
                .map_err(|e| format!("读语音表失败：{e}"))?
                .into_iter()
                .find(|v| v.id() == voice || v.name() == voice);
            if let Some(v) = wanted {
                t.set_voice(&v).map_err(|e| format!("选语音失败：{e}"))?;
            }
        }

        // 前端沿用 Web Speech 的语速口径（1.0 是正常，0.9–1.45 常用）。各后端的
        // 取值范围差别很大（macOS 是词/分钟，WinRT 是 0.5–6.0 的倍数），所以按
        // 后端自报的 normal/min/max 折算，而不是写死系数。
        let normal = t.normal_rate();
        let target = normal * rate as f32;
        let clamped = target.clamp(t.min_rate(), t.max_rate());
        let _ = t.set_rate(clamped);

        // 第二个参数是 interrupt：新的一句打断上一句，对应 Web Speech 的 cancel()
        t.speak(text, true).map_err(|e| format!("朗读失败：{e}"))?;
        Ok(())
    }

    /// 当前这句念完了没有。前端轮询它来串起「一段念完再念下一段」。
    pub fn finished(&mut self) -> bool {
        match self.inner.as_ref() {
            None => true,
            // 问不出来就当它结束，否则朗读会卡在这一句上再也走不下去
            Some(t) => !t.is_speaking().unwrap_or(false),
        }
    }

    pub fn voices(&self) -> Vec<NativeVoice> {
        let Some(t) = self.inner.as_ref() else {
            return Vec::new();
        };
        let Ok(list) = t.voices() else {
            return Vec::new();
        };
        list.into_iter()
            .filter(|v| v.language().primary_language().eq_ignore_ascii_case("zh"))
            .map(|v| NativeVoice {
                better: is_better(&v.name()),
                name: v.id(),
                lang: v.language().to_string(),
            })
            .collect()
    }
}

pub type TtsState = Mutex<Tts>;

#[cfg(test)]
mod tests {
    use super::*;

    /// 有没有中文语音取决于这台机器装了什么，不能断言；但**初始化与枚举本身
    /// 必须在三个平台上都不炸**——原来直接调 macOS 的 `say`，另外两个平台
    /// 根本没跑过这条路径。
    #[test]
    fn listing_voices_works_on_every_platform() {
        let tts = Tts::default();
        let voices = tts.voices();
        eprintln!("本机中文语音 {} 个", voices.len());
        for v in &voices {
            assert!(!v.name.is_empty(), "语音标识不该为空");
            assert!(
                v.lang.to_lowercase().starts_with("zh"),
                "过滤后不该混进非中文语音：{}",
                v.lang
            );
        }
    }

    #[test]
    fn empty_text_is_a_no_op() {
        let mut tts = Tts::default();
        assert!(tts.speak("   ", "", 1.0).is_ok(), "空白文本应当直接返回");
    }
}
