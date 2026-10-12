import { defineConfig } from "vite";
// @ts-expect-error type error without @types/node package
import process from "node:process";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
const host = process.env.TAURI_DEV_HOST;

// Tauri 用自定义协议加载前端：必须用相对资源路径，否则发行包里是白屏。
export default defineConfig(() => ({
  base: "./",
  clearScreen: false,
  plugins: [react(), tailwindcss()],
  server: {
    port: 1450,
    strictPort: true,
    host: host || false,
  },
}));
