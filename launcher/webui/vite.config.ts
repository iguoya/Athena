import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// 端口与 src-tauri/tauri.conf.json 的 devUrl 约定一致（1510）。
export default defineConfig({
  plugins: [react()],
  clearScreen: false,
  server: {
    port: 1510,
    strictPort: true,
  },
  build: {
    target: "es2022",
  },
});
