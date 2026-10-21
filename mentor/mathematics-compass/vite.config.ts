import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { fileURLToPath } from "node:url";
// @ts-expect-error type error without @types/node package
import process from "node:process";
const host = process.env.TAURI_DEV_HOST;

// Tauri 用自定义协议加载前端：必须用相对资源路径，否则发行包里是白屏。
// 渲染栈按摘星基线（ADR 0138 决策 3）：Tailwind v4 + 令牌，端口固定 1523。
export default defineConfig(() => ({
  base: "./",
  clearScreen: false,
  plugins: [react(), tailwindcss()],
  resolve: { alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) } },
  envPrefix: ["VITE_", "TAURI_ENV_"],
  build: { target: "es2022", sourcemap: false },
  server: {
    port: 1523,
    strictPort: true,
    host: host || false,
    hmr: host ? { protocol: "ws", host, port: 11523 } : undefined,
    watch: { ignored: ["**/src-tauri/**"] },
  },
}));
