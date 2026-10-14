import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
// @ts-expect-error type error without @types/node package
import process from "node:process";
const host = process.env.TAURI_DEV_HOST;

// Tauri 用自定义协议加载前端：必须用相对资源路径，否则发行包里是白屏。
export default defineConfig(() => ({
  base: "./",
  clearScreen: false,
  plugins: [react()],
  server: {
    port: 1517,
    strictPort: true,
    host: host || false,
    hmr: host ? { protocol: "ws", host, port: 11517 } : undefined,
    // 上游克隆（几千个文件）与 Rust 侧变更不走前端 HMR
    watch: { ignored: ["**/src-tauri/**", "**/upstream/**"] },
  },
}));
