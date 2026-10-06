import { create } from "zustand";
import { formatHash, HOME, parseHash, type Location } from "./router";

export type ThemeId = "sky" | "paper";

export const THEMES: { id: ThemeId; label: string; swatch: [string, string] }[] = [
  { id: "sky", label: "晴空", swatch: ["#1f6feb", "#f4f8fc"] },
  { id: "paper", label: "暖纸", swatch: ["#d9481f", "#fbf5ea"] },
];

const THEME_KEY = "polaris.theme";

// 主题名是每个人自己的偏好，不是学习进度或账号（ADR 0012 的边界之外），存在本机浏览器存储里。
// 存取都可能失败（隐私模式、被清理），所以一律兜底，界面照常渲染。
function readTheme(): ThemeId {
  try {
    const stored = localStorage.getItem(THEME_KEY);
    if (stored === "sky" || stored === "paper") return stored;
  } catch {
    /* 没有存储也能用 */
  }
  return "sky";
}

function applyTheme(theme: ThemeId): void {
  document.documentElement.dataset.theme = theme;
  try {
    localStorage.setItem(THEME_KEY, theme);
  } catch {
    /* 同上 */
  }
}

interface AppState {
  loc: Location;
  /** 悬停预览与选中是同一个「聚焦」概念的两档：悬停是临时的，选中是钉住的。 */
  hoverId: string | null;
  /** 被点开的连线，格式 from>to。 */
  edgeKey: string | null;
  theme: ThemeId;
  drawerWide: boolean;

  go(loc: Location, replace?: boolean): void;
  selectNode(id: string | null): void;
  setHover(id: string | null): void;
  setEdge(key: string | null): void;
  setTheme(theme: ThemeId): void;
  toggleDrawerWide(): void;
}

export const useApp = create<AppState>((set, get) => ({
  loc: typeof location === "undefined" ? HOME : parseHash(location.hash),
  hoverId: null,
  edgeKey: null,
  theme: readTheme(),
  drawerWide: false,

  go(loc, replace = false) {
    const hash = formatHash(loc);
    if (replace) history.replaceState(null, "", hash);
    else if (location.hash !== hash) location.hash = hash;
    set({ loc, edgeKey: null, hoverId: null });
  },
  selectNode(id) {
    const { loc, go } = get();
    if (loc.view === "home") return;
    go({ ...loc, nodeId: id ?? undefined }, true);
  },
  setHover: (hoverId) => set({ hoverId }),
  setEdge: (edgeKey) => set({ edgeKey }),
  setTheme(theme) {
    applyTheme(theme);
    set({ theme });
  },
  toggleDrawerWide: () => set((state) => ({ drawerWide: !state.drawerWide })),
}));

// 初始主题在首屏渲染前就要生效，避免闪一下默认主题。
applyTheme(useApp.getState().theme);

// 浏览器后退 / 手动改地址栏：哈希变了，位置跟着变。
if (typeof window !== "undefined") {
  window.addEventListener("hashchange", () => {
    useApp.setState({ loc: parseHash(location.hash), edgeKey: null, hoverId: null });
  });
}
