/** 系统语音。念课表里的原文，不另写讲稿（ADR 0018）。 */

let current: SpeechSynthesisUtterance | null = null;
let gen = 0;

/** 语速与音色是很个人的偏好，交给使用者自己定（ADR 0011 第 4 节第 3 项） */
const RATE_KEY = "math.speech.rate";
const VOICE_KEY = "math.speech.voice";

/** 老年音色排到最后，但不再从候选里删掉——多留几个备选，好坏由使用者自己判断 */
const OLD = /grandma|grandpa/i;
/**
 * 默认要年轻女声。Flo、Sandy、Shelley 是 macOS 较新的几个女声，比旧版默认的
 * Tingting 年轻；Eddy、Reed、Rocko 是男声，排在后面备选而不是默认。
 * 系统 API 不给性别字段，这个次序按已知音色人工排定，听感因人而异——
 * 所以界面上给了试听和切换，不锁死。
 */
const PREFER = ["Shelley", "Meijia", "美嘉", "Sandy", "Flo", "Tingting", "婷婷", "Sinji", "善怡", "Eddy", "Reed", "Rocko"];

export interface VoiceInfo {
  name: string;
  lang: string;
  label?: string;
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

function regionOf(lang: string): string {
  const l = lang.toLowerCase();
  if (l.includes("tw")) return "台湾";
  if (l.includes("hk")) return "香港";
  return "大陆";
}

/** 名字里带这些词的是系统下载的增强版，音质明显好过默认的压缩版 */
const BETTER = /premium|enhanced|siri|增强|高级|高音质|优质|neural/i;

/** 全部中文语音，按「音质更好 → 年轻 → 老年」排序；地区一并标出来 */
export function listVoices(): VoiceInfo[] {
  if (!window.speechSynthesis) return [];
  const zh = window.speechSynthesis
    .getVoices()
    .filter((v) => v.lang.toLowerCase().startsWith("zh"));
  const rank = (v: SpeechSynthesisVoice) => {
    if (BETTER.test(v.name)) return -100; // 下载来的增强版一律排最前
    if (OLD.test(v.name)) return 900;
    const i = PREFER.findIndex((p) => v.name.toLowerCase().includes(p.toLowerCase()));
    return i < 0 ? 500 : i;
  };
  const seen = new Set<string>();
  return zh
    .filter((v) => {
      const k = `${v.name}|${v.lang}`;
      return seen.has(k) ? false : (seen.add(k), true);
    })
    .sort((a, b) => rank(a) - rank(b))
    .map((v) => ({
      name: v.name,
      lang: v.lang,
      label: `${v.name}（${regionOf(v.lang)}${BETTER.test(v.name) ? " · 增强" : ""}）`,
    }));
}

/** 系统里有没有装增强版中文语音——没有的话音质就只能是压缩版的水平 */
export function hasBetterVoice(): boolean {
  return listVoices().some((v) => BETTER.test(v.name));
}

const UPGRADED_KEY = "math.speech.upgraded";

export function getVoiceName(): string {
  const avail = listVoices();
  const saved = load(VOICE_KEY, "");
  const best = avail.find((v) => BETTER.test(v.name));

  // 系统里新装了高音质语音时，自动换过去一次——刚装好的人不该还得自己去下拉里翻。
  // 只做一次，之后他再手动选什么就是什么。
  if (best && load(UPGRADED_KEY, "") !== "1") {
    save(UPGRADED_KEY, "1");
    save(VOICE_KEY, best.name);
    return best.name;
  }
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
      u.rate = getRate();
      // 不动音高：抬高只会更像卡通，不会更自然
      u.pitch = 1;
      // 先认语音，再让 lang 跟着它走。反过来先设 lang 的话，WebKit 有按 lang
      // 重选语音、把显式指定的那个覆盖掉的情况——表现就是「设置里选了高音质，
      // 听起来还是原来那个」。选不到时才退回按语言让系统挑。
      const want = getVoiceName();
      const v = want ? window.speechSynthesis.getVoices().find((x) => x.name === want) : undefined;
      if (v) {
        u.voice = v;
        u.lang = v.lang;
      } else {
        u.lang = "zh-CN";
      }
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

/**
 * 把正文转成能听的句子：去掉重点标记，把符号换成中文读法。
 * 讲解正文不是为朗读写的（walkthrough 的 say 才是），所以要过这一道。
 */
/**
 * 下标与上标。严谨那一侧全是 `a₁₁`、`Rⁿ`、`T(eᵢ)` 这样的写法，原样交给 TTS
 * 会被跳过或读成怪音——念出来就成了「a 的行列式」这种缺了主语的句子。
 * 一律摊平成普通字符，用空格隔开：`a₁₁` 念「a 一 一」，比连读「a 十一」准确。
 */
const SUB: Record<string, string> = {
  "₀": "0", "₁": "1", "₂": "2", "₃": "3", "₄": "4",
  "₅": "5", "₆": "6", "₇": "7", "₈": "8", "₉": "9",
  "ᵢ": "i", "ⱼ": "j", "ₖ": "k", "ₘ": "m", "ₙ": "n",
};
const SUP: Record<string, string> = {
  "⁰": "0", "¹": "1", "⁴": "4", "⁵": "5",
  "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9",
  "ⁿ": "n", "ᵐ": "m", "ᵀ": "转置",
};

export function speakable(src: string): string {
  return (
    src
      // 重点标记与行内代码的包裹符号，念出来是噪音
      .replace(/\*\*(.+?)\*\*/g, "$1")
      .replace(/==(.+?)==/g, "$1")
      // 反引号先一次清干净，再做后面的替换。原先是先做矩阵替换、再按
      // `内容` 成对去反引号——矩阵那条会吃掉右边那一个而留下左边那一个，
      // 后面的配对就整体错位，念出来多一个孤零零的反引号。
      .replace(/`/g, "")
      // 矩阵写法：[[1,2],[3,4]] → 「矩阵 1 2 3 4」。注意逗号后允许空格——
      // 原先的正则要求 ],[ 紧挨着，而正文里写的是 ], [，于是一直没匹配上，
      // 方括号被原样念了出来。
      .replace(/\[\[([^\]]+)\]\s*,\s*\[([^\]]+)\]\]/g, (_m, a, b) =>
        `矩阵 ${a.replace(/,/g, " ")} ${b.replace(/,/g, " ")}`)
      // |det A| 这类绝对值记号，竖线念出来是噪音
      .replace(/\|([^|]{1,24})\|/g, "$1 的绝对值")
      // 平方立方有现成的说法，其余上标摊平
      .replace(/²/g, " 平方")
      .replace(/³/g, " 立方")
      .replace(/[⁰¹⁴⁵⁶⁷⁸⁹ⁿᵐᵀ]/g, (c) => ` ${SUP[c] ?? ""}`)
      // 前后都留空格：a₁₁a₂₂ 要念成「a 一 一 a 二 二」，只在前面加会粘成「1a」
      .replace(/[₀₁₂₃₄₅₆₇₈₉ᵢⱼₖₘₙ]/g, (c) => ` ${SUB[c] ?? ""} `)
      // 坐标 (1, 2) 读成「1 逗号 2」会很怪，改读「1 2」
      .replace(/\((-?\d+(?:\.\d+)?),\s*(-?\d+(?:\.\d+)?)\)/g, "$1 $2")
      .replace(/([^<>=!])=([^=])/g, "$1 等于 $2")
      .replace(/×/g, " 乘 ")
      .replace(/·/g, " 乘 ")
      .replace(/÷/g, " 除以 ")
      .replace(/≠/g, " 不等于 ")
      .replace(/⟺/g, " 等价于 ")
      .replace(/→/g, " 变成 ")
      .replace(/…/g, " 等等 ")
      // 减号分两种读法。原先一律念「负」，于是 a₁₁a₂₂ − a₁₂a₂₁ 被念成「…负…」，
      // 听着像另一个式子。判据是前面紧挨着的是不是一个「量」——数字、字母、右括号
      // 才算中缀减法；跟在「等于」后面的是负号，不能一起吃掉。
      .replace(/([0-9a-zA-Z)）\]])\s*[−–]\s*/g, "$1 减 ")
      .replace(/[−–]/g, "负 ")
      .replace(/λ/g, "拉姆达")
      // 原文里多半已经写了「矩阵」二字，上面的替换会再加一个
      .replace(/矩阵\s*矩阵/g, "矩阵")
      .replace(/\s+/g, " ")
      .trim()
  );
}

export function speechAvailable(): boolean {
  return typeof window !== "undefined" && "speechSynthesis" in window;
}
