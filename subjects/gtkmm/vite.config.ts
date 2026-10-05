import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
// @ts-expect-error type error without @types/node package
import process from "node:process";
const host = process.env.TAURI_DEV_HOST;

// Tauri 用自定义协议加载前端：必须用相对资源路径，否则发行包里是白屏。
export default defineConfig(() => ({
  base: "./",
  clearScreen: false,
  plugins: [react(), tailwindcss()],
  server: {
    port: 1460,
    strictPort: true,
    host: host || false,
    hmr: host
      ? {
          protocol: "ws",
          host,
          port: 1461,
        }
      : undefined,
    watch: {
      // 演示工程与 Rust 侧变更不走前端 HMR
      ignored: ["**/src-tauri/**", "**/demos/**"],
    },
  },
}));
