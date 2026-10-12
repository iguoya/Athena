// 皮肤:与 math-tools skins 同构——一套组件,令牌换氛围(见 style.css 的 --tk-* 令牌)。
// 三套浅色(应用不使用暗色):电路(默认,嵌入式绿)/ 晨读(暖纸衬线)/ 草稿(米纸手写)。

export const SKINS = [
  { id: 'board', name: '电路', hint: '基板绿 · 网格', dot: 'linear-gradient(135deg, #0e8a6d, #14b8a6)' },
  { id: 'dawn', name: '晨读', hint: '暖纸 · 衬线', dot: 'linear-gradient(135deg, #f59e0b, #f43f5e)' },
  { id: 'draft', name: '草稿', hint: '米纸 · 手写体', dot: 'linear-gradient(135deg, #e0765a, #4d9e6a)' },
] as const

export type SkinId = (typeof SKINS)[number]['id']

const KEY = 'esd-skin'

export function applySkin(skin: SkinId): void {
  document.documentElement.dataset.style = skin
  localStorage.setItem(KEY, skin)
}

export function currentSkin(): SkinId {
  const saved = localStorage.getItem(KEY) as SkinId | null
  // 旧值不在清单里时自然回退到默认浅色
  return saved && SKINS.some((s) => s.id === saved) ? saved : 'board'
}
