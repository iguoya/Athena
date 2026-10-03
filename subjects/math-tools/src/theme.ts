/** 皮肤:与拾阶 skins 同构——一套组件,令牌换氛围(见 style.css 的 --tk-* 令牌)。 */

export const SKINS = [
  { id: 'sky', name: '晴空', hint: '浅蓝网格', dot: 'linear-gradient(135deg, #5b63f5, #06b6d4)' },
  { id: 'dawn', name: '晨读', hint: '暖纸 · 衬线', dot: 'linear-gradient(135deg, #f59e0b, #f43f5e)' },
  { id: 'draft', name: '草稿', hint: '米纸 · 手写体', dot: 'linear-gradient(135deg, #e0765a, #4d9e6a)' },
] as const

export type SkinId = (typeof SKINS)[number]['id']

const KEY = 'mt-skin'

export function applySkin(skin: SkinId): void {
  document.documentElement.dataset.style = skin
  localStorage.setItem(KEY, skin)
}

export function currentSkin(): SkinId {
  const saved = localStorage.getItem(KEY) as SkinId | null
  // 旧值(cosmos 暗色皮肤)不在清单里时自然回退到默认浅色
  return saved && SKINS.some((s) => s.id === saved) ? saved : 'sky'
}
