import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { fileURLToPath } from "node:url";
// @ts-expect-error type error without @types/node package
import process from "node:process";
const host = process.env.TAURI_DEV_HOST;

export default defineConfig(() => ({
  base: "./",
  clearScreen: false,
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
      "@content": fileURLToPath(new URL("./content", import.meta.url)),
      "@athena/maps": fileURLToPath(
        new URL("../../packages/maps/src", import.meta.url),
      ),
    },
  },
  envPrefix: ["VITE_", "TAURI_ENV_"],
  build: { target: "es2022", sourcemap: false },
  server: {
    port: 1516,
    strictPort: true,
    host: host || false,
    hmr: host ? { protocol: "ws", host, port: 1616 } : undefined,
    watch: { ignored: ["**/src-tauri/**"] },
    fs: {
      allow: [
        fileURLToPath(new URL("../..", import.meta.url)),
        fileURLToPath(new URL("../../packages/maps", import.meta.url)),
      ],
    },
  },
}));
