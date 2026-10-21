// 无框架（vanilla TS）应用的挂载入口（ADR 0172 接入清单第 6 条的 vanilla 变体）。
// 独立成无 JSX 的 .ts：vanilla 应用的 tsconfig 不开 jsx，解析到 .tsx 会报 TS6142。
// 用 createElement 而不是 JSX，应用两行接入、不需要自己引入 React：
//   import { mountAppUpdate } from "@athena/app-update/mount";
//   mountAppUpdate();
import { createElement } from "react";
import { createRoot } from "react-dom/client";
import { AppUpdate } from "./AppUpdate";

export function mountAppUpdate(container?: HTMLElement): () => void {
  const host = container ?? document.createElement("div");
  if (!container) {
    host.dataset.athenaAppUpdate = "";
    document.body.appendChild(host);
  }
  createRoot(host).render(createElement(AppUpdate));
  return () => createRoot(host).unmount();
}
