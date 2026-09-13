/** 系统语音。念课表里的原文，不另写讲稿（ADR 0018）。 */

let current: SpeechSynthesisUtterance | null = null;
let gen = 0;

/** 语速与音色是很个人的偏好，交给使用者自己定（ADR 0011 第 4 节第 3 项） */
const RATE_KEY = "math.speech.rate";
const VOICE_KEY = "math.speech.voice";

/** 系统里这两个是明确的老年音色，不进候选 */
const EXCLUDE = /grandma|grandpa/i;
/**
 * 默认要年轻女声。Flo、Sandy、Shelley 是 macOS 较新的几个女声，比旧版默认的
 * Tingting 年轻；Eddy、Reed、Rocko 是男声，排在后面备选而不是默认。
 * 系统 API 不给性别字段，这个次序按已知音色人工排定，听感因人而异——
 * 所以界面上给了试听和切换，不锁死。
 */
const PREFER = ["Sandy", "Shelley", "Flo", "Meijia", "Tingting", "Sinji", "Eddy", "Reed", "Rocko"];

export interface VoiceInfo {
  name: string;
  lang: string;
}

function load(key: string, fallback: string): string {
  try {
    return localStorage.getItem(key) ?? fallback;
  } catch {
    return fallback;
  }
}
function save(key: string, value: string) {
  try {
    localStorage.setItem(key, value);
  } catch {
    /* 隐私模式下存不了就算了，不影响播放 */
  }
}

export function getRate(): number {
  const n = Number(load(RATE_KEY, "1.1"));
  return Number.isFinite(n) && n > 0 ? n : 1.1;
}
export function setRate(r: number) {
  save(RATE_KEY, String(r));
}

/** 系统可用的中文语音，已排除老年音色，按「年轻优先」排好序 */
export function listVoices(): VoiceInfo[] {
  if (!window.speechSynthesis) return [];
  const zh = window.speechSynthesis
    .getVoices()
    .filter((v) => v.lang.toLowerCase().startsWith("zh") && !EXCLUDE.test(v.name));
  const rank = (n: string) => {
    const i = PREFER.findIndex((p) => n.toLowerCase().includes(p.toLowerCase()));
    return i < 0 ? PREFER.length : i;
  };
  const seen = new Set<string>();
  return zh
    .filter((v) => (seen.has(v.name) ? false : (seen.add(v.name), true)))
    .sort((a, b) => rank(a.name) - rank(b.name))
    .map((v) => ({ name: v.name, lang: v.lang }));
}

export function getVoiceName(): string {
  const saved = load(VOICE_KEY, "");
  const avail = listVoices();
  if (saved && avail.some((v) => v.name === saved)) return saved;
  return avail[0]?.name ?? "";
}
export function setVoiceName(name: string) {
  save(VOICE_KEY, name);
}

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
      u.rate = getRate();
      // 音高略高于默认，听感更年轻；再高就发尖了
      u.pitch = 1.08;
      const want = getVoiceName();
      const v = window.speechSynthesis.getVoices().find((x) => x.name === want);
      if (v) u.voice = v;
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

/** 部分 WebView 首次 getVoices() 返回空，要等系统把列表填好 */
export function voicesReady(): Promise<void> {
  if (!window.speechSynthesis) return Promise.resolve();
  if (window.speechSynthesis.getVoices().length) return Promise.resolve();
  return new Promise((resolve) => {
    const done = () => resolve();
    window.speechSynthesis.addEventListener("voiceschanged", done, { once: true });
    window.setTimeout(done, 1200);
  });
}

export function speechAvailable(): boolean {
  return typeof window !== "undefined" && "speechSynthesis" in window;
}
