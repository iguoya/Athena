// 只为在浏览器里核对渲染效果：把 Tauri 命令换成读静态 JSON，产物全部落在 dist/（已 gitignore）。
// 正式验证仍走 tauri:dev，这个只用来看样式。
import { cpSync, existsSync, mkdirSync, readdirSync, writeFileSync } from "node:fs";
const js = readdirSync("dist/assets").find((f) => f.endsWith(".js"));
const css = readdirSync("dist/assets").find((f) => f.endsWith(".css"));
mkdirSync("dist/content", { recursive: true });
for (const d of ["lessons"]) if (existsSync(`content/${d}`)) cpSync(`content/${d}`, `dist/content/${d}`, { recursive: true });
cpSync("content/curriculum.json", "dist/content/curriculum.json");
writeFileSync(
  "dist/preview.html",
  `<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <link rel="stylesheet" href="./assets/${css}" />
    <title>翁恺 C 语言（预览）</title>
    <script>
      const attempts = [];
      window.__TAURI_INTERNALS__ = {
        transformCallback: (cb) => { window.__cbs = window.__cbs || []; window.__cbs.push(cb); return window.__cbs.length; },
        unregisterCallback: () => {},
        invoke: async (cmd, args) => {
          if (cmd === "get_curriculum") return (await fetch("./content/curriculum.json")).json();
          if (cmd === "get_lesson") return (await fetch("./content/lessons/" + args.lessonId + ".json")).json();
          if (cmd === "get_attempts") return attempts;
          if (cmd === "record_attempt") { attempts.push({ knowledge_id: args.knowledgeId, item_id: args.itemId, correct: args.correct, answered_at: Math.floor(Date.now() / 1000) }); return null; }
          if (cmd === "load_marks") return null;
          return null; // player_*、save_marks、plugin:event|listen 等：预览里没有播放器，当作成功
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
