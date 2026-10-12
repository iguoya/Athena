import '@fontsource-variable/sora'
import '@fontsource-variable/jetbrains-mono'
import '@fontsource/zcool-kuaile'
import '@fontsource/noto-sans-sc'
import '@fontsource/noto-sans-sc/500.css'
import '@fontsource/noto-sans-sc/700.css'
import 'katex/dist/katex.min.css'
import './style.css'
import React from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import { applySkin, currentSkin } from './theme'

applySkin(currentSkin())

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
