// 语音练习只负责系统朗读和一次会话内的录音回听。
// 不上传、不落库，也不把音量或时长冒充发音评分。
// 朗读只采用美式英语音色；同一口音里的具体声音和语速交给使用者自选。

import { isDesktop } from "./backend";

const RATE_KEY = "english.speech.rate";
const VOICE_KEY = "english.speech.voice";
const SAMPLE = "The library provides students with a quiet place to study.";

export const RATE_OPTIONS: Array<[number, string]> = [
  [0.7, "慢"],
  [0.86, "稍慢"],
  [1.0, "常速"],
  [1.15, "稍快"],
];

const PREFER = [
  "Samantha",
  "Nicky",
  "Ava",
  "Allison",
  "Aria",
  "Jenny",
  "Zoe",
  "Flo",
  "Sandy",
  "Shelley",
  "Aaron",
  "Guy",
  "Davis",
  "Andrew",
  "Alex",
  "Google US English",
];

const BETTER = /premium|enhanced|siri|neural|natural|超自然|增强|高级|高音质|优质/i;

export interface VoiceInfo {
  name: string;
  lang: string;
  label: string;
}

function load(key: string, fallback: string): string {
  try {
    return localStorage.getItem(key) ?? fallback;
  } catch {
    return fallback;
  }
}

function save(key: string, value: string): void {
  try {
    localStorage.setItem(key, value);
  } catch {
    /* 隐私模式存不了也不影响朗读 */
  }
}

export function canSpeak(): boolean {
  return "speechSynthesis" in window && "SpeechSynthesisUtterance" in window;
}

function isAmericanEnglish(voice: SpeechSynthesisVoice): boolean {
  const tag = voice.lang.toLowerCase().replace("_", "-");
  const name = voice.name.toLowerCase();
  if (/(british|uk english|australian|indian|irish|south african|english \(uk\)|english \(au\)|english \(in\)|english \(ie\))/i.test(voice.name)) {
    return false;
  }
  if (tag.startsWith("en-us")) {
    return true;
  }
  return tag === "en" && /google us english|united states|american/i.test(name);
}

export function listEnglishVoices(): VoiceInfo[] {
  if (!canSpeak()) return [];
  const voices = window.speechSynthesis.getVoices().filter(isAmericanEnglish);
  const rank = (voice: SpeechSynthesisVoice): number => {
    if (BETTER.test(voice.name)) return -100;
    const index = PREFER.findIndex((name) => voice.name.toLowerCase().includes(name.toLowerCase()));
    return index < 0 ? 500 : index;
  };
  const seen = new Set<string>();
  return voices
    .filter((voice) => {
      const key = `${voice.name}|${voice.lang}`;
      return seen.has(key) ? false : (seen.add(key), true);
    })
    .sort((a, b) => rank(a) - rank(b) || a.name.localeCompare(b.name))
    .map((voice) => ({
      name: voice.name,
      lang: voice.lang,
      label: `${voice.name}${BETTER.test(voice.name) ? " · 增强" : ""}`,
    }));
}

export function getRate(): number {
  const value = Number(load(RATE_KEY, "0.86"));
  return Number.isFinite(value) && value > 0 ? value : 0.86;
}

export function setRate(rate: number): void {
  save(RATE_KEY, String(rate));
}

export function getVoiceName(): string {
  const available = listEnglishVoices();
  const saved = load(VOICE_KEY, "");
  if (saved && available.some((voice) => voice.name === saved)) {
    return saved;
  }
  return available[0]?.name ?? "";
}

export function setVoiceName(name: string): void {
  save(VOICE_KEY, name);
}

export function speakEnglish(text: string): void {
  if (!canSpeak() || text.trim().length === 0 || listEnglishVoices().length === 0) {
    throw new Error("当前系统没有可用的美式英语朗读音色");
  }
  window.speechSynthesis.cancel();
  window.setTimeout(() => {
    const utterance = new SpeechSynthesisUtterance(text);
    const want = getVoiceName();
    utterance.lang = "en-US";
    utterance.rate = getRate();
    utterance.pitch = 1;
    const voice = window.speechSynthesis
      .getVoices()
      .find((candidate) => candidate.name === want && isAmericanEnglish(candidate));
    if (voice) {
      utterance.voice = voice;
    }
    window.speechSynthesis.speak(utterance);
  }, 40);
}

export function previewVoice(): void {
  speakEnglish(SAMPLE);
}

export function stopSpeaking(): void {
  if (canSpeak()) {
    window.speechSynthesis.cancel();
  }
}

/** 部分 WebView 首次 getVoices() 为空，要等系统把列表填好。 */
export function voicesReady(): Promise<void> {
  if (!canSpeak()) return Promise.resolve();
  if (window.speechSynthesis.getVoices().length) return Promise.resolve();
  return new Promise((resolve) => {
    const done = () => resolve();
    window.speechSynthesis.addEventListener("voiceschanged", done, { once: true });
    window.setTimeout(done, 1200);
  });
}

export async function openExternal(url: string): Promise<void> {
  if (isDesktop) {
    const { openUrl } = await import("@tauri-apps/plugin-opener");
    await openUrl(url);
    return;
  }
  window.open(url, "_blank", "noopener,noreferrer");
}

export class VoiceRecorder {
  private recorder: MediaRecorder | null = null;
  private stream: MediaStream | null = null;
  private chunks: Blob[] = [];
  private playbackUrl: string | null = null;
  private generation = 0;

  supported(): boolean {
    return Boolean(navigator.mediaDevices?.getUserMedia) && "MediaRecorder" in window;
  }

  active(): boolean {
    return this.recorder?.state === "recording";
  }

  async start(): Promise<void> {
    this.reset();
    const generation = this.generation;
    if (!this.supported()) {
      throw new Error("当前 WebView 不支持录音");
    }
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: { echoCancellation: true, noiseSuppression: true },
    });
    if (generation !== this.generation) {
      stream.getTracks().forEach((track) => track.stop());
      throw new Error("录音请求已取消");
    }
    this.stream = stream;
    this.chunks = [];
    this.recorder = new MediaRecorder(this.stream);
    this.recorder.addEventListener("dataavailable", (event) => {
      if (event.data.size > 0) {
        this.chunks.push(event.data);
      }
    });
    this.recorder.start();
  }

  async stop(): Promise<string> {
    const current = this.recorder;
    if (!current || current.state !== "recording") {
      throw new Error("当前没有正在进行的录音");
    }
    return new Promise((resolve, reject) => {
      current.addEventListener(
        "stop",
        () => {
          try {
            const type = current.mimeType || this.chunks[0]?.type || "audio/webm";
            const blob = new Blob(this.chunks, { type });
            if (blob.size === 0) {
              reject(new Error("没有录到可回放的声音"));
              return;
            }
            if (this.playbackUrl) {
              URL.revokeObjectURL(this.playbackUrl);
            }
            this.playbackUrl = URL.createObjectURL(blob);
            resolve(this.playbackUrl);
          } finally {
            this.stopTracks();
            this.recorder = null;
          }
        },
        { once: true },
      );
      current.stop();
    });
  }

  reset(): void {
    this.generation += 1;
    if (this.recorder?.state === "recording") {
      this.recorder.stop();
    }
    this.recorder = null;
    this.stopTracks();
    this.chunks = [];
    if (this.playbackUrl) {
      URL.revokeObjectURL(this.playbackUrl);
      this.playbackUrl = null;
    }
  }

  private stopTracks(): void {
    this.stream?.getTracks().forEach((track) => track.stop());
    this.stream = null;
  }
}
