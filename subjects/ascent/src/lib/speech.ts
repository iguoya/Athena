// 朗读走系统 TTS：Web Speech API（WebView2 用 Windows 本地语音），离线可用，不打包音频（ADR 0022）。
// voices 列表在部分浏览器上是异步就绪的，speak 时拿不到就先用默认语音。

let cachedVoice: SpeechSynthesisVoice | null = null;

function pickVoice(): SpeechSynthesisVoice | null {
  if (cachedVoice) return cachedVoice;
  if (typeof speechSynthesis === "undefined") return null;
  const voices = speechSynthesis.getVoices();
  if (!voices.length) return null;
  const en = voices.filter((v) => v.lang.toLowerCase().startsWith("en"));
  cachedVoice =
    en.find((v) => /en[-_]US/i.test(v.lang) && v.localService) ?? en.find((v) => v.localService) ?? en[0] ?? null;
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
  speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  const voice = pickVoice();
  if (voice) u.voice = voice;
  u.lang = voice?.lang ?? "en-US";
  u.rate = rate;
  speechSynthesis.speak(u);
}

export function speechAvailable() {
  return typeof speechSynthesis !== "undefined";
}
