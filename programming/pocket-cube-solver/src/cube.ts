// 讲解页里画魔方用的小模型。它和 exercise/06-solver/cube.cc 是同一个想法：
// 24 张贴纸各有三维位置和朝外方向，转一个面就是把这一层绕轴转 90°。
// 两边各写一份，一致性由 scripts/check.py 用 scripts/cube_golden.json 里的黄金向量核对。

export type Vec = [number, number, number];
export type Stickers = number[]; // 24 格，每格是颜色号 0..5，对应面 U R F D L B

export const FACES = ["U", "R", "F", "D", "L", "B"] as const;
export const NORMALS: Vec[] = [
  [0, 1, 0],
  [1, 0, 0],
  [0, 0, 1],
  [0, -1, 0],
  [-1, 0, 0],
  [0, 0, -1],
];

// 展开图每面按"从左到右、从上到下"数 4 格，第 r 行第 c 列对应的角块坐标。
function makeSlot(face: number, r: number, c: number): { pos: Vec; normal: Vec } {
  const y = r === 0 ? 1 : -1;
  switch (face) {
    case 0:
      return { pos: [c === 0 ? -1 : 1, 1, r === 0 ? -1 : 1], normal: NORMALS[0] };
    case 1:
      return { pos: [1, y, c === 0 ? 1 : -1], normal: NORMALS[1] };
    case 2:
      return { pos: [c === 0 ? -1 : 1, y, 1], normal: NORMALS[2] };
    case 3:
      return { pos: [c === 0 ? -1 : 1, -1, r === 0 ? 1 : -1], normal: NORMALS[3] };
    case 4:
      return { pos: [-1, y, c === 0 ? -1 : 1], normal: NORMALS[4] };
    default:
      return { pos: [c === 0 ? 1 : -1, y, -1], normal: NORMALS[5] };
  }
}

export const SLOTS = Array.from({ length: 24 }, (_, i) => makeSlot(Math.floor(i / 4), Math.floor((i % 4) / 2), i % 2));

const eq = (a: Vec, b: Vec) => a[0] === b[0] && a[1] === b[1] && a[2] === b[2];
export function slotIndex(pos: Vec, normal: Vec): number {
  return SLOTS.findIndex((s) => eq(s.pos, pos) && eq(s.normal, normal));
}

const dot = (a: Vec, b: Vec) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const cross = (a: Vec, b: Vec): Vec => [
  a[1] * b[2] - a[2] * b[1],
  a[2] * b[0] - a[0] * b[2],
  a[0] * b[1] - a[1] * b[0],
];

// 从轴的尖端往原点看，顺时针转 90°：v' = a(a·v) - a×v。
function rotateCw(v: Vec, a: Vec): Vec {
  const k = dot(a, v);
  const c = cross(a, v);
  return [a[0] * k - c[0], a[1] * k - c[1], a[2] * k - c[2]];
}

export type Move = { face: number; turns: number };

// src[i]：转完之后第 i 格的颜色来自转之前的哪一格。
const cache = new Map<string, number[]>();
function permutation(m: Move): number[] {
  const key = `${m.face}:${m.turns}`;
  const hit = cache.get(key);
  if (hit) return hit;
  const axis = NORMALS[m.face];
  const src = Array.from({ length: 24 }, (_, i) => i);
  SLOTS.forEach((s, i) => {
    if (dot(s.pos, axis) !== 1) return;
    let p = s.pos;
    let n = s.normal;
    for (let t = 0; t < m.turns; t += 1) {
      p = rotateCw(p, axis);
      n = rotateCw(n, axis);
    }
    src[slotIndex(p, n)] = i;
  });
  cache.set(key, src);
  return src;
}

export function solved(): Stickers {
  return Array.from({ length: 24 }, (_, i) => Math.floor(i / 4));
}

export function perform(s: Stickers, m: Move): Stickers {
  const src = permutation(m);
  return src.map((from) => s[from]);
}

export function parse(text: string): Move[] {
  const out: Move[] = [];
  const pattern = /([URFDLB])(2|'|3)?/g;
  const cleaned = text.replace(/\s+/g, "");
  let used = 0;
  for (const m of cleaned.matchAll(pattern)) {
    used += m[0].length;
    const turns = m[2] === "2" ? 2 : m[2] === "'" || m[2] === "3" ? 3 : 1;
    out.push({ face: FACES.indexOf(m[1] as (typeof FACES)[number]), turns });
  }
  if (used !== cleaned.length) throw new Error(`记号写错了：${text}`);
  return out;
}

export function label(m: Move): string {
  return FACES[m.face] + (m.turns === 2 ? "2" : m.turns === 3 ? "'" : "");
}

export function run(start: Stickers, moves: Move[]): Stickers {
  return moves.reduce(perform, start);
}

// 这一步转的那一层：面上的 4 张加四周侧面的 4 张。
export function layerSlots(m: Move): number[] {
  const axis = NORMALS[m.face];
  return SLOTS.flatMap((s, i) => (dot(s.pos, axis) === 1 ? [i] : []));
}

// 颜色：和 gtkmm 程序里的 view::rgb 同一套。
export const COLORS = ["#ffd500", "#ff5800", "#009b48", "#f4f4f4", "#b71234", "#0046ad"];
export const UNPAINTED = "#8c929a";

// ---- 立体图：把 24 张贴纸投影到平面，只画朝向观察者的 ----

export type Quad = { points: [number, number][]; slot: number; depth: number };

export function isometric(yaw = 0.62, pitch = 0.5): Quad[] {
  const toward: Vec = [Math.sin(yaw) * Math.cos(pitch), Math.sin(pitch), Math.cos(yaw) * Math.cos(pitch)];
  const r0 = cross([0, 1, 0], toward);
  const rl = Math.hypot(...r0);
  const right: Vec = [r0[0] / rl, r0[1] / rl, r0[2] / rl];
  const up = cross(toward, right);
  const quads: Quad[] = [];
  SLOTS.forEach((s, slot) => {
    if (dot(s.normal, toward) <= 1e-6) return;
    const t1: Vec = s.normal[0] !== 0 ? [0, 1, 0] : [1, 0, 0];
    const t2 = cross(s.normal, t1);
    const centre: Vec = [s.pos[0] + s.normal[0], s.pos[1] + s.normal[1], s.pos[2] + s.normal[2]];
    const corner = (a: number, b: number): [number, number] => {
      const p: Vec = [
        centre[0] + 0.92 * (a * t1[0] + b * t2[0]),
        centre[1] + 0.92 * (a * t1[1] + b * t2[1]),
        centre[2] + 0.92 * (a * t1[2] + b * t2[2]),
      ];
      return [dot(p, right), -dot(p, up)];
    };
    quads.push({ points: [corner(1, 1), corner(1, -1), corner(-1, -1), corner(-1, 1)], slot, depth: dot(centre, toward) });
  });
  return quads.sort((a, b) => a.depth - b.depth);
}

// ---- 阶段的完成条件（和 solver.cc 里的 layer_done、top_oriented、is_solved 对应）----

const CORNER_POS: Vec[] = [
  [1, 1, 1], [-1, 1, 1], [-1, 1, -1], [1, 1, -1],
  [1, -1, 1], [-1, -1, 1], [-1, -1, -1], [1, -1, -1],
];

// 8 个角块位置上的三张贴纸：从朝上或朝下的那张开始顺时针数。
export function cornerSlots(c: number): [number, number, number] {
  const [x, y, z] = CORNER_POS[c];
  const mirrored = x * y * z < 0;
  return [
    slotIndex([x, y, z], [0, y, 0]),
    slotIndex([x, y, z], mirrored ? [0, 0, z] : [x, 0, 0]),
    slotIndex([x, y, z], mirrored ? [x, 0, 0] : [0, 0, z]),
  ];
}

export const isSolved = (s: Stickers) => s.every((v, i) => v === Math.floor(i / 4));
export const layerDone = (s: Stickers) => [4, 5, 6, 7].every((c) => cornerSlots(c).every((i) => s[i] === Math.floor(i / 4)));
export const topOriented = (s: Stickers) => [0, 1, 2, 3].every((i) => s[i] === 0);
