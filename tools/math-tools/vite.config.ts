import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { fileURLToPath } from 'node:url'

// 与摘星(ascent)同构(ADR 0138 决策 3):别名 @ 指向 src,端口固定,Tauri 相关环境变量前缀放行。
export default defineConfig({
  base: './',
  plugins: [react(), tailwindcss()],
  resolve: { alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) } },
  clearScreen: false,
  envPrefix: ['VITE_', 'TAURI_ENV_'],
  build: { target: 'es2022', sourcemap: false },
  server: {
    port: 1451,
    strictPort: true,
    watch: { ignored: ['**/src-tauri/**'] },
  },
})
