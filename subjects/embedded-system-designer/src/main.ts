import '@fontsource-variable/sora'
import '@fontsource-variable/jetbrains-mono'
import '@fontsource/zcool-kuaile'
import '@fontsource/noto-sans-sc'
import '@fontsource/noto-sans-sc/500.css'
import '@fontsource/noto-sans-sc/700.css'
import 'katex/dist/katex.min.css'
import './style.css'
import { createApp } from 'vue'
import App from './App.vue'
import { applySkin, currentSkin } from './theme'

applySkin(currentSkin())

createApp(App).mount('#app')
