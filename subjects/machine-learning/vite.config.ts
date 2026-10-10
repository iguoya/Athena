import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Tauri 用自定义协议加载前端：必须用相对资源路径，否则发行包里是白屏。
export default defineConfig({
  base: "./",
  clearScreen: false,
  plugins: [react()],
  server: {
    port: 1506,
    strictPort: true,
  },
});
