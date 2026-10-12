// 只为在浏览器里核对渲染效果：把 Tauri 命令换成读静态 JSON，产物全部落在
// dist/（已 gitignore）。正式验证仍走 tauri:dev，这个只用来看样式。
import { readdirSync, writeFileSync, mkdirSync, copyFileSync } from "node:fs";
const js = readdirSync("dist/assets").find((f) => f.endsWith(".js"));
const css = readdirSync("dist/assets").find((f) => f.endsWith(".css"));
mkdirSync("dist/content", { recursive: true });
for (const f of readdirSync("content")) {
  if (f.endsWith(".json")) copyFileSync(`content/${f}`, `dist/content/${f}`);
}
writeFileSync(
  "dist/preview.html",
  `<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <link rel="stylesheet" href="./assets/${css}" />
    <title>数学学习（预览）</title>
    <script>
      window.__TAURI_INTERNALS__ = {
        invoke: async (cmd, args) => {
          if (cmd === "load_curriculum") return (await fetch("./content/curriculum.json")).json();
          if (cmd === "load_diagnostics") return (await fetch("./content/diagnostics.json")).json();
          if (cmd === "load_all_progress") return [];
          if (cmd === "load_all_predictions") return [];
          // 引擎的假回包：只用来核对界面怎么显示三种判定。真实的 Rust↔Python
          // 链路由 src-tauri/src/engine.rs 的单元测试验证，两段合起来才算覆盖。
          if (cmd === "engine_status")
            return { ready: true, detail: "就绪（预览假引擎）", sympy: "1.14.0-fake", import_ms: 0, warmup_ms: 0 };
          if (cmd === "engine_equiv") {
            const b = String(args?.b ?? "");
            if (b.includes("?")) return { ok: false, error: "没看懂：预览假引擎只认几种写法" };
            if (b.includes("unknown")) return { ok: true, verdict: "unknown", note: "数值处处吻合，但没能化简证明", ms: 42 };
            if (b.includes("bad")) return { ok: true, verdict: "different", ms: 12 };
            return { ok: true, verdict: "equal", ms: 8 };
          }
          return null;
        },
      };
    </script>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="./assets/${js}"></script>
  </body>
</html>
`,
);
console.log(`preview: dist/preview.html → ${js} / ${css}`);
