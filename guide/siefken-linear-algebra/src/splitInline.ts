// 行内标记的切分：把「文字 **粗** *斜* $公式$」切成片段，供界面渲染与 check-math 共用。
// 公式的收尾 $ 必须在花括号深度 0——\text{ … $x$ … } 里嵌套的 $ 属于内层，
// 同一条规则在 scripts/sync_upstream.py 的 split_math 里也有一份，两边必须一致。

export type Seg = { k: "text" | "math"; v: string };

export function splitInline(s: string): Seg[] {
  const out: Seg[] = [];
  let buf = "";
  let i = 0;
  while (i < s.length) {
    const c = s[i];
    if (c === "\\" && i + 1 < s.length) {
      buf += s.slice(i, i + 2);
      i += 2;
      continue;
    }
    if (c === "$") {
      let k = i + 1;
      let depth = 0;
      while (k < s.length) {
        if (s[k] === "\\") {
          k += 2;
          continue;
        }
        if (s[k] === "{") depth++;
        else if (s[k] === "}") depth--;
        else if (s[k] === "$" && depth <= 0) break;
        k++;
      }
      if (k < s.length) {
        if (buf) out.push({ k: "text", v: buf });
        buf = "";
        out.push({ k: "math", v: s.slice(i + 1, k) });
        i = k + 1;
        continue;
      }
    }
    buf += c;
    i++;
  }
  if (buf) out.push({ k: "text", v: buf });
  return out;
}
