import '@fontsource-variable/sora'
import '@fontsource-variable/fraunces'
import '@fontsource/zcool-kuaile'
import '@fontsource/noto-sans-sc'
import '@fontsource-variable/jetbrains-mono'
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
