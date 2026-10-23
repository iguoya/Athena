// 习题核对点的答案解析：学习者怎么写，就怎么认。
// 支持 整数/小数/分数、根号（sqrt(2) 或 √2）、π（pi）、乘方（^）、括号，以及用逗号/分号/空格分隔的多个数
// （向量、矩阵按行展开）。写法有歧义时（如 "1 -2" 是两个数还是 1−2），所有合理读法都试，任一读法与答案相符就算对。

type Tok = { t: "num"; v: number } | { t: "name"; v: string } | { t: "op"; v: string };

function tokenize(s: string): Tok[] | null {
  const out: Tok[] = [];
  let i = 0;
  while (i < s.length) {
    const c = s[i];
    if (c === " ") { i++; continue; }
    const m = /^(\d+(?:\.\d+)?|\.\d+)/.exec(s.slice(i));
    if (m) { out.push({ t: "num", v: parseFloat(m[1]) }); i += m[1].length; continue; }
    const n = /^[a-z]+/i.exec(s.slice(i));
    if (n) { out.push({ t: "name", v: n[0].toLowerCase() }); i += n[0].length; continue; }
    if ("+-*/^()".includes(c)) { out.push({ t: "op", v: c }); i++; continue; }
    return null;
  }
  return out;
}

/** 递归下降求值；失败返回 null。 */
export function evalExpr(src: string): number | null {
  const toks = tokenize(src);
  if (!toks || toks.length === 0) return null;
  let p = 0;
  const peek = () => toks[p];
  const isOp = (v: string) => peek()?.t === "op" && (peek() as { v: string }).v === v;
  const fail = Symbol("fail");
  const expr = (): number => {
    let v = term();
    while (isOp("+") || isOp("-")) { const o = (toks[p++] as { v: string }).v; const r = term(); v = o === "+" ? v + r : v - r; }
    return v;
  };
  const term = (): number => {
    let v = unary();
    for (;;) {
      if (isOp("*")) { p++; v *= unary(); }
      else if (isOp("/")) { p++; v /= unary(); }
      else if (peek() && (peek().t === "num" || peek().t === "name" || isOp("("))) v *= power(); // 隐含乘法：2sqrt(2)、3pi、2(x)
      else return v;
    }
  };
  const unary = (): number => {
    if (isOp("-")) { p++; return -unary(); }
    if (isOp("+")) { p++; return unary(); }
    return power();
  };
  const power = (): number => {
    const b = atom();
    if (isOp("^")) { p++; return Math.pow(b, unary()); }
    return b;
  };
  const atom = (): number => {
    const t = toks[p++];
    if (!t) throw fail;
    if (t.t === "num") return t.v;
    if (t.t === "name") {
      if (t.v === "pi") return Math.PI;
      if (t.v === "e") return Math.E;
      if (t.v === "sqrt") {
        if (!isOp("(")) throw fail;
        p++; const v = expr(); if (!isOp(")")) throw fail; p++;
        return Math.sqrt(v);
      }
      throw fail;
    }
    if (t.v === "(") { const v = expr(); if (!isOp(")")) throw fail; p++; return v; }
    throw fail;
  };
  try {
    const v = expr();
    if (p !== toks.length || !Number.isFinite(v)) return null;
    return v;
  } catch (e) {
    if (e === fail) return null;
    throw e;
  }
}

function normalize(s: string): string {
  return s
    .replace(/[，；、]/g, ",")
    .replace(/[−–—－]/g, "-")
    .replace(/[×·]/g, "*")
    .replace(/÷/g, "/")
    .replace(/√\s*\(/g, "sqrt(")
    .replace(/√\s*([0-9.]+)/g, "sqrt($1)")
    .replace(/π/g, "pi")
    .replace(/[（［\[{]/g, "(")
    .replace(/[）］\]}]/g, ")")
    .trim();
}

/** 去掉把整个答案括起来的一层括号：(1, 2, 3) → 1, 2, 3；(1+2) 不动。 */
function stripOuter(s: string): string {
  while (s.startsWith("(") && s.endsWith(")")) {
    let depth = 0, wraps = true;
    for (let i = 0; i < s.length; i++) {
      if (s[i] === "(") depth++;
      else if (s[i] === ")") depth--;
      if (depth === 0 && i < s.length - 1) { wraps = false; break; }
    }
    if (!wraps) break;
    const inner = s.slice(1, -1);
    if (!/[,;]/.test(inner) && !/\)\s*,|,\s*\(/.test(inner)) { // 括号里是单个表达式就留着，交给求值
      if (!/\)\s*\(/.test(inner)) break;
    }
    s = inner.trim();
  }
  return s;
}

/** 所有合理读法下得到的数列表（去重）。 */
export function candidates(raw: string): number[][] {
  let s = normalize(raw);
  const outs: number[][] = [];
  let depth = 0;
  for (const c of s) { if (c === "(") depth++; else if (c === ")") depth--; if (depth < 0) return []; }
  if (depth !== 0) return []; // 括号不配对：不猜
  const push = (xs: Array<number | null>) => { if (xs.length && xs.every((x) => x !== null)) outs.push(xs as number[]); };
  // 读法 0：整个是一个表达式
  push([evalExpr(s)]);
  s = stripOuter(s);
  // 把多层括号（矩阵按行写成 (1,2),(3,4)）拍平
  const flat = s.replace(/\)\s*,?\s*\(/g, ",").replace(/^\(|\)$/g, "");
  // 读法 1：按逗号/分号切
  if (/[,;]/.test(flat)) push(flat.split(/[,;]/).map((x) => x.trim()).filter(Boolean).map(evalExpr));
  // 读法 2：按空白切（运算符两侧的空格先并掉）
  const tight = flat.replace(/\s*([*/^])\s*/g, "$1");
  if (/\s/.test(tight) && !/[,;]/.test(tight)) {
    push(tight.split(/\s+/).filter(Boolean).map(evalExpr));
    // "1 - 2" 的另一读法：运算符粘在后一个数上才是新的数
    push(tight.replace(/\s*([+])\s*/g, "$1").split(/\s+/).filter(Boolean).map(evalExpr));
  }
  return outs;
}

export function numbersMatch(got: number[], want: number[], tol = 1e-6): boolean {
  return got.length === want.length && got.every((v, i) => Math.abs(v - want[i]) <= tol * Math.max(1, Math.abs(want[i])));
}

/** 学习者的输入是否与答案相符（任一读法即可）。 */
export function answerMatches(input: string, want: number[]): boolean {
  return candidates(input).some((c) => numbersMatch(c, want));
}
