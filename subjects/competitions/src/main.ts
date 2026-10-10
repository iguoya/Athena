import { openUrl } from "@tauri-apps/plugin-opener";
import data from "../content/competitions.json";

type Allow = "yes" | "no" | "per-event" | "pending";
type Level = "official" | "notice" | "report" | "pending";

interface Competition {
  id: string;
  name: string;
  direction: string;
  organizer: string | null;
  students: Allow;
  public: Allow;
  note: string;
  window: string | null;
  url: string | null;
  courses: string[];
  verify: { level: Level; source: string | null; date: string | null };
}

const directions: { id: string; title: string }[] = data.directions;
const competitions = data.competitions as Competition[];

const ALLOW_TEXT: Record<Allow, string> = {
  yes: "可参加",
  no: "不可参加",
  "per-event": "以单场规则为准",
  pending: "待核对",
};

const LEVEL_TEXT: Record<Level, string> = {
  official: "官方章程",
  notice: "往届/院校通知",
  report: "第三方报道",
  pending: "未核对",
};

// 赛事规则一年一变：核对超过一年就提示重新核对，而不是静默沿用（ADR 0114）。
const STALE_DAYS = 365;

let who: "all" | "students" | "public" = "all";
let direction = "all";

function el<K extends keyof HTMLElementTagNameMap>(
  tag: K,
  className?: string,
  text?: string,
): HTMLElementTagNameMap[K] {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function isStale(date: string | null): boolean {
  if (!date) return false;
  const age = (Date.now() - new Date(date).getTime()) / 86_400_000;
  return age > STALE_DAYS;
}

// 在 Tauri 里交给系统浏览器；在普通浏览器预览时退回新标签页。
function open(url: string) {
  if ("__TAURI_INTERNALS__" in window) {
    void openUrl(url);
  } else {
    window.open(url, "_blank", "noopener");
  }
}

// 「可参」只认 yes 与 per-event：待核对的不算，免得把没查过的当成能报名。
function matches(c: Competition): boolean {
  if (direction !== "all" && c.direction !== direction) return false;
  if (who === "students") return c.students === "yes" || c.students === "per-event";
  if (who === "public") return c.public === "yes" || c.public === "per-event";
  return true;
}

function badge(label: string, value: Allow): HTMLElement {
  const b = el("span", `badge ${value}`);
  b.append(el("span", "badge-label", label), el("span", "badge-value", ALLOW_TEXT[value]));
  return b;
}

function card(c: Competition): HTMLElement {
  const root = el("article", "card");
  const head = el("div", "card-head");
  head.append(el("h2", undefined, c.name));
  const dir = directions.find((d) => d.id === c.direction);
  if (dir) head.append(el("span", "tag", dir.title));
  root.append(head);

  const badges = el("div", "badges");
  badges.append(badge("在校生", c.students), badge("社会人士", c.public));
  root.append(badges);

  root.append(el("p", "note", c.note));

  const meta = el("dl", "meta");
  if (c.organizer) meta.append(el("dt", undefined, "主办"), el("dd", undefined, c.organizer));
  if (c.window) meta.append(el("dt", undefined, "时间"), el("dd", undefined, c.window));
  if (meta.childElementCount) root.append(meta);

  if (c.courses.length) {
    const courses = el("div", "courses");
    courses.append(el("span", "courses-label", "对应课程"));
    for (const name of c.courses) courses.append(el("span", "course", name));
    root.append(courses);
  }

  const foot = el("footer", "card-foot");
  const v = c.verify;
  const check = el("span", `verify ${v.level}`);
  check.textContent = v.date ? `${LEVEL_TEXT[v.level]} · 核对于 ${v.date}` : LEVEL_TEXT[v.level];
  if (isStale(v.date)) check.append(el("span", "stale", "可能过期"));
  foot.append(check);

  const actions = el("span", "actions");
  if (v.source) {
    const src = el("button", "link", "来源");
    src.addEventListener("click", () => open(v.source!));
    actions.append(src);
  }
  if (c.url) {
    const site = el("button", "link primary", "官网");
    site.addEventListener("click", () => open(c.url!));
    actions.append(site);
  }
  foot.append(actions);
  root.append(foot);
  return root;
}

function render() {
  const list = document.querySelector<HTMLElement>("#list")!;
  const shown = competitions.filter(matches);
  list.replaceChildren(...shown.map(card));
  const pending = shown.filter((c) => c.verify.level === "pending").length;
  document.querySelector("#count")!.textContent =
    `${shown.length} 项` + (pending ? `，其中 ${pending} 项资格待核对` : "");
}

function setup() {
  const select = document.querySelector<HTMLSelectElement>("#direction")!;
  select.append(new Option("全部方向", "all"));
  for (const d of directions) select.append(new Option(d.title, d.id));
  select.addEventListener("change", () => {
    direction = select.value;
    render();
  });

  const buttons = document.querySelectorAll<HTMLButtonElement>(".seg button");
  buttons.forEach((button) => {
    button.addEventListener("click", () => {
      who = button.dataset.who as typeof who;
      buttons.forEach((b) => b.classList.toggle("on", b === button));
      render();
    });
  });
  render();
}

setup();
