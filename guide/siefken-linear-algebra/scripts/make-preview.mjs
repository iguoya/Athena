// 只为在浏览器里核对渲染效果：把 Tauri 命令换成读静态 JSON，产物全部落在 dist/（已 gitignore）。
// 正式验证仍走 tauri:dev，这个只用来看样式。
import { cpSync, existsSync, mkdirSync, readdirSync, writeFileSync } from "node:fs";
const js = readdirSync("dist/assets").find((f) => f.endsWith(".js"));
const css = readdirSync("dist/assets").find((f) => f.endsWith(".css"));
mkdirSync("dist/content", { recursive: true });
for (const d of ["sections", "checks", "figures"]) if (existsSync(`content/${d}`)) cpSync(`content/${d}`, `dist/content/${d}`, { recursive: true });
cpSync("content/curriculum.json", "dist/content/curriculum.json");
writeFileSync(
  "dist/preview.html",
  `<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <link rel="stylesheet" href="./assets/${css}" />
    <title>Siefken 线性代数（预览）</title>
    <script>
      const attempts = [];
      window.__TAURI_INTERNALS__ = {
        invoke: async (cmd, args) => {
          if (cmd === "get_curriculum") return (await fetch("./content/curriculum.json")).json();
          if (cmd === "get_section") return (await fetch("./content/sections/" + args.sectionId + ".json")).json();
          if (cmd === "get_checks") {
            const r = await fetch("./content/checks/" + args.sectionId + ".json");
            return r.ok ? r.json() : null;
          }
          if (cmd === "get_figure") {
            const r = await fetch("./content/figures/" + args.figId + ".svg");
            return r.ok ? r.text() : null;
          }
          if (cmd === "get_attempts") return attempts;
          if (cmd === "record_attempt") { attempts.push({ knowledge_id: args.knowledgeId, item_id: args.itemId, correct: args.correct, answered_at: Math.floor(Date.now() / 1000) }); return null; }
          return null;
        },
      };
    </script>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="./assets/${js}"></script>
  </body>
</html>
`,
);
console.log(`preview: dist/preview.html → ${js} / ${css}`);
