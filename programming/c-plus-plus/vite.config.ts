import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { fileURLToPath } from "node:url";

// Tauri 用自定义协议加载前端：必须用相对资源路径，否则发行包里是白屏。
export default defineConfig({
  base: "./",
  clearScreen: false,
  plugins: [react(), tailwindcss()],
  resolve: { alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) } },
  envPrefix: ["VITE_", "TAURI_ENV_"],
  build: { target: "es2022", sourcemap: false },
  server: {
    port: 1512,
    strictPort: true,
    // 公共呈现件在仓库根 packages/viz（ADR 0137）：Vite 默认不放行工作区之外的文件。
    fs: { allow: [".", "../../packages/viz"] },
    watch: { ignored: ["**/src-tauri/**", "**/content/cases/**"] },
  },
});
