import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import tailwindcss from "@tailwindcss/vite";

// Tauri 用自定义协议加载前端：必须用相对资源路径，否则发行包里是白屏。
export default defineConfig({
  base: "./",
  clearScreen: false,
  plugins: [vue(), tailwindcss()],
  server: {
    port: 1494,
    strictPort: true,
  },
});
