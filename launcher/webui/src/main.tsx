import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App";

// 工具条等全局样式：骨架阶段集中在这里，组件化时再拆。
const style = document.createElement("style");
style.textContent = `
.toolbar {
  position: fixed; top: 0; left: 0; right: 0; z-index: 10;
  display: flex; align-items: center; gap: 12px;
  padding: 10px 16px;
  background: rgba(251, 251, 253, 0.82);
  backdrop-filter: blur(8px);
}
.brand { font-weight: 600; letter-spacing: 1px; color: #1c1c1e; }
.hint { color: #8a8a8e; font-size: 12px; margin-left: auto; }
.toolbar button {
  background: #ffffff; color: #1c1c1e; border: 1px solid #d5d9ea;
  border-radius: 8px; padding: 6px 14px; cursor: pointer; font-size: 13px;
}
.toolbar button:hover { background: #eef0fa; }
.status { display: grid; place-items: center; height: 100vh; color: #8a8a8e; }
.tile {
  display: flex; flex-direction: column; align-items: center; gap: 8px;
  padding: 14px 8px; border-radius: 12px; cursor: pointer;
  border: 1px solid transparent; width: 116px;
}
.tile:hover { border-color: #5468a4; background: rgba(84, 104, 164, 0.08); }
.tile img, .tile .fallback {
  width: 56px; height: 56px; object-fit: contain;
  display: grid; place-items: center; border-radius: 14px;
  font-weight: 600; color: white; font-size: 22px;
  transition: transform 120ms ease-out;
}
.tile:hover img, .tile:hover .fallback { transform: scale(1.15); }
.tile .name { font-size: 12px; color: #3a3a44; text-align: center;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 112px; }
.tile .dot { width: 8px; height: 8px; border-radius: 50%; }
.tile[data-state="ready"] .dot { background: #2e9e44; }
.tile[data-state="starting"] .dot { background: #e8940f; }
.tile[data-state="stopped"] .dot { background: #b0b4c8; }
`;
document.head.appendChild(style);

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
