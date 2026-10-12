import { defineConfig } from "vite";
// @ts-expect-error type error without @types/node package
import process from "node:process";
const host = process.env.TAURI_DEV_HOST;

// Tauri 用自定义协议加载前端：必须用相对资源路径，否则发行包里是白屏。
export default defineConfig(() => ({
  base: "./",
  clearScreen: false,
  server: {
    port: 1501,
    strictPort: true,
    // 公共呈现件在仓库根 packages/viz（ADR 0137）：Vite 默认不放行工作区之外的文件。
    fs: { allow: [".", "../../packages/viz"] },
    host: host || false,
    hmr: host
      ? {
          protocol: "ws",
          host,
          port: 1601,
        }
      : undefined,
    watch: {
      // cases 若被「运行」或其它路径写回磁盘，不能触发 HMR/整页刷新
      ignored: ["**/src-tauri/**", "**/content/cases/**"],
    },
  },
}));
