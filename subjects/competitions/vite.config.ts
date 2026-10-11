import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { fileURLToPath } from "node:url";
// @ts-expect-error type error without @types/node package
import process from "node:process";
const host = process.env.TAURI_DEV_HOST;

// Tauri 用自定义协议加载前端：必须用相对资源路径，否则发行包里是白屏。
// 其余与摘星（ascent）同构（ADR 0138 决策 3）：别名 @ 指向 src，端口固定。
export default defineConfig(() => ({
  base: "./",
  clearScreen: false,
  plugins: [react(), tailwindcss()],
  resolve: { alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) } },
  envPrefix: ["VITE_", "TAURI_ENV_"],
  build: { target: "es2022", sourcemap: false },
  server: {
    port: 1502,
    strictPort: true,
    host: host || false,
    hmr: host ? { protocol: "ws", host, port: 1602 } : undefined,
    watch: { ignored: ["**/src-tauri/**"] },
  },
}));
