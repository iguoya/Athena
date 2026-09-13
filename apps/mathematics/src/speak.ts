/** 系统语音。念课表里的原文，不另写讲稿（ADR 0018）。 */

let current: SpeechSynthesisUtterance | null = null;
let gen = 0;

export function stopSpeech() {
  gen += 1;
  current = null;
  window.speechSynthesis?.cancel();
}

export function speak(text: string): Promise<void> {
  if (!window.speechSynthesis) {
    return Promise.resolve();
  }
  const mine = ++gen;
  current = null;
  window.speechSynthesis.cancel();
  return new Promise((resolve) => {
    // cancel 之后立刻 speak，部分 WebView 会静默丢掉这一句
    window.setTimeout(() => {
      if (mine !== gen) {
        resolve();
        return;
      }
      const u = new SpeechSynthesisUtterance(text);
      u.lang = "zh-CN";
      u.rate = 0.95;
      const zh = window.speechSynthesis
        .getVoices()
        .find((v) => v.lang.toLowerCase().startsWith("zh"));
      if (zh) u.voice = zh;
      u.onend = () => {
        if (current === u) current = null;
        resolve();
      };
      u.onerror = () => {
        if (current === u) current = null;
        resolve();
      };
      current = u;
      window.speechSynthesis.speak(u);
    }, 40);
  });
}

export function speechAvailable(): boolean {
  return typeof window !== "undefined" && "speechSynthesis" in window;
}
