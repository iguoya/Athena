// 朗读走系统 TTS：Web Speech API（WebView2 用 Windows 本地语音），离线可用，不打包音频（ADR 0022）。
// 发音固定美式优先：en-US 本地语音 > en-US 在线语音 > 其他英语语音。单词、句子、短语、
// 短文共用这一个入口；慢速跟读用 speak(text, 0.6)。
// voices 列表在部分浏览器上是异步就绪的，speak 时拿不到就先用默认语音。

let cachedVoice: SpeechSynthesisVoice | null = null;

/** 美式发音优先级：en-US 本地 > en-US 在线 > 其他英语本地 > 其他英语。 */
function voiceRank(v: SpeechSynthesisVoice): number {
  const us = /en[-_]us/i.test(v.lang);
  return (us ? 2 : 0) + (v.localService ? 1 : 0);
}

function pickVoice(): SpeechSynthesisVoice | null {
  if (cachedVoice) return cachedVoice;
  if (typeof speechSynthesis === "undefined") return null;
  const voices = speechSynthesis.getVoices();
  if (!voices.length) return null;
  const en = voices.filter((v) => v.lang.toLowerCase().startsWith("en")).sort((a, b) => voiceRank(b) - voiceRank(a));
  cachedVoice = en[0] ?? null;
  return cachedVoice;
}

if (typeof speechSynthesis !== "undefined") {
  speechSynthesis.onvoiceschanged = () => {
    cachedVoice = null;
    pickVoice();
  };
}

/** Speak English text aloud; safe no-op when the platform has no speech engine. */
export function speak(text: string, rate = 0.95) {
  if (typeof speechSynthesis === "undefined") return;
  if (!text.trim()) return;
  speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  const voice = pickVoice();
  if (voice) u.voice = voice;
  u.lang = voice?.lang ?? "en-US";
  u.rate = rate;
  speechSynthesis.speak(u);
}

/** 慢速跟读用：比正常语速明显慢，但保持自然连读的停顿。 */
export const SLOW_RATE = 0.6;

export function speechAvailable() {
  return typeof speechSynthesis !== "undefined";
}
