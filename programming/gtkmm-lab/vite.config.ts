import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Tauri 用自定义协议加载前端：必须用相对资源路径，否则发行包里是白屏。
export default defineConfig({
  base: "./",
  clearScreen: false,
  plugins: [react()],
  server: {
    port: 1527,
    strictPort: true,
    // 公共呈现件在仓库根 packages/viz（ADR 0137）：Vite 默认不放行工作区之外的文件。
    fs: { allow: [".", "../../packages/viz"] },
    // 案例目录是只读的原样代码，运行也不会写回；仍排除，免得编辑器里改它触发整页刷新。
    watch: { ignored: ["**/src-tauri/**", "**/content/cases/**"] },
  },
});
