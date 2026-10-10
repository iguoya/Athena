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
  background: rgba(13, 16, 32, 0.75);
  backdrop-filter: blur(8px);
}
.brand { font-weight: 600; letter-spacing: 1px; }
.hint { color: #8a90b8; font-size: 12px; margin-left: auto; }
.toolbar button {
  background: #232849; color: #e8eaf6; border: 1px solid #3a4070;
  border-radius: 8px; padding: 6px 14px; cursor: pointer; font-size: 13px;
}
.toolbar button:hover { background: #323a6b; }
.status { display: grid; place-items: center; height: 100vh; color: #8a90b8; }
.tile {
  display: flex; flex-direction: column; align-items: center; gap: 8px;
  padding: 14px 8px; border-radius: 12px; cursor: pointer;
  border: 1px solid transparent; width: 116px;
}
.tile:hover { border-color: #5468a4; background: rgba(84, 104, 164, 0.12); }
.tile img, .tile .fallback {
  width: 56px; height: 56px; object-fit: contain;
  display: grid; place-items: center; border-radius: 14px;
  font-weight: 600; color: white; font-size: 22px;
  transition: transform 120ms ease-out;
}
.tile:hover img, .tile:hover .fallback { transform: scale(1.15); }
.tile .name { font-size: 12px; color: #c9cdee; text-align: center;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 112px; }
.tile .dot { width: 8px; height: 8px; border-radius: 50%; }
.tile[data-state="ready"] .dot { background: #4caf50; }
.tile[data-state="starting"] .dot { background: #ff9800; }
.tile[data-state="stopped"] .dot { background: #5a5f7a; }
`;
document.head.appendChild(style);

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
