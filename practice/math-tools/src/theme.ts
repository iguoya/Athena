/** 皮肤:与拾阶 skins 同构——一套组件,令牌换氛围(见 style.css 的 --tk-* 令牌)。 */

export const SKINS = [
  { id: 'cosmos', name: '星穹', hint: '深空网格 · 霓虹', dot: 'linear-gradient(135deg, #8b5cf6, #22d3ee)' },
  { id: 'dawn', name: '晨读', hint: '暖纸 · 衬线', dot: 'linear-gradient(135deg, #f59e0b, #f43f5e)' },
  { id: 'draft', name: '草稿', hint: '米纸 · 手写体', dot: 'linear-gradient(135deg, #e0765a, #4d9e6a)' },
] as const

export type SkinId = (typeof SKINS)[number]['id']

const KEY = 'mt-skin'

export function applySkin(skin: SkinId): void {
  document.documentElement.dataset.style = skin
  // 皮肤自带亮暗:星穹是暗色,其余浅色;组件里的 dark: 变体继续工作
  document.documentElement.classList.toggle('dark', skin === 'cosmos')
  localStorage.setItem(KEY, skin)
}

export function currentSkin(): SkinId {
  const saved = localStorage.getItem(KEY) as SkinId | null
  return saved && SKINS.some((s) => s.id === saved) ? saved : 'cosmos'
}
