import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "node:path";

// Tauri 要求固定端口，且不能让开发服务器清屏吞掉日志。
// 内容（content/）在应用根目录而不在 src/ 里，前端直接导入，不复制（ADR 0015 决策 2）。
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(import.meta.dirname, "src"),
      "@content": path.resolve(import.meta.dirname, "content"),
    },
  },
  // Tauri 用自定义协议加载前端：必须用相对资源路径，否则发行包里是白屏。
  base: "./",
  clearScreen: false,
  server: { port: 1470, strictPort: true, watch: { ignored: ["**/src-tauri/**", "**/legacy-qt/**"] } },
  envPrefix: ["VITE_", "TAURI_ENV_"],
  // 内容（polaris.json）按设计打进主包：应用本地运行，不需要为它拆分加载。
  build: { target: "es2022", sourcemap: false, chunkSizeWarningLimit: 1500 },
  test: { include: ["src/**/*.test.ts"], environment: "node" },
});
