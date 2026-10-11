// 画布视口的纯数学：缩放、适配、居中。与 React 无关，便于单测。

export interface Viewport {
  /** 内容原点在视口里的位置（像素）。 */
  x: number;
  y: number;
  /** 缩放。 */
  k: number;
}

export interface Size {
  w: number;
  h: number;
}

export const MIN_K = 0.25;
export const MAX_K = 2;

export const clampK = (k: number): number => Math.min(MAX_K, Math.max(MIN_K, k));

/** 以视口里的 (cx, cy) 为不动点缩放：光标下的内容点缩放前后位置不变。 */
export function zoomAt(view: Viewport, factor: number, cx: number, cy: number): Viewport {
  const k = clampK(view.k * factor);
  const ratio = k / view.k;
  return { k, x: cx - (cx - view.x) * ratio, y: cy - (cy - view.y) * ratio };
}

/** 让整张内容完整出现在视口里并居中；放大不超过 maxK，免得小图被撑得过大。 */
export function fitViewport(content: Size, view: Size, padding = 24, maxK = 1): Viewport {
  const k = clampK(Math.min(maxK, (view.w - padding * 2) / content.w, (view.h - padding * 2) / content.h));
  return { k, x: (view.w - content.w * k) / 2, y: (view.h - content.h * k) / 2 };
}

/**
 * 按宽度适配：整张图的宽度恰好放进视口，从顶部开始看。高图不会被缩得看不清，
 * 往下看靠平移——比整体塞进视口更适合列很长的图。
 */
export function fitWidthViewport(content: Size, view: Size, padding = 24, maxK = 1): Viewport {
  const k = clampK(Math.min(maxK, (view.w - padding * 2) / content.w));
  return { k, x: (view.w - content.w * k) / 2, y: padding };
}

/**
 * 选中的节点已经在可见区域里（四周留 margin）就不动，免得点一下画面就跳；
 * 不在，才把它移到可见区域的中心。`insetRight` 同 centerOn。
 */
export function ensureVisible(
  view: Viewport,
  rect: { x: number; y: number; w: number; h: number },
  size: Size,
  insetRight = 0,
  margin = 48,
): Viewport {
  const left = rect.x * view.k + view.x;
  const top = rect.y * view.k + view.y;
  const right = left + rect.w * view.k;
  const bottom = top + rect.h * view.k;
  const visibleW = size.w - insetRight;
  const inside = left >= margin && top >= margin && right <= visibleW - margin && bottom <= size.h - margin;
  return inside ? view : centerOn(view, { x: rect.x + rect.w / 2, y: rect.y + rect.h / 2 }, size, insetRight);
}

/**
 * 把内容里的一点放到可见区域的中心。`insetRight` 是被抽屉等盖住的宽度——
 * 可见区域只算到它左边，这样选中的节点不会被抽屉挡住。
 */
export function centerOn(view: Viewport, point: { x: number; y: number }, size: Size, insetRight = 0): Viewport {
  const visibleW = Math.max(1, size.w - insetRight);
  return { k: view.k, x: visibleW / 2 - point.x * view.k, y: size.h / 2 - point.y * view.k };
}

export function sameViewport(a: Viewport, b: Viewport): boolean {
  return a.x === b.x && a.y === b.y && a.k === b.k;
}
