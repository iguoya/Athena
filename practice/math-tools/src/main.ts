import '@fontsource-variable/sora'
import '@fontsource/noto-sans-sc'
import '@fontsource-variable/jetbrains-mono'
import './style.css'
import { createApp } from 'vue'
import App from './App.vue'

const saved = localStorage.getItem('mt-theme')
if (saved === 'light') {
  document.documentElement.classList.remove('dark')
}

createApp(App).mount('#app')
