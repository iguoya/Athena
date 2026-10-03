import '@fontsource-variable/sora'
import '@fontsource-variable/fraunces'
import '@fontsource/zcool-kuaile'
import '@fontsource/noto-sans-sc'
import '@fontsource-variable/jetbrains-mono'
import './style.css'
import { createApp } from 'vue'
import App from './App.vue'
import { applySkin, currentSkin } from './theme'

applySkin(currentSkin())

createApp(App).mount('#app')
