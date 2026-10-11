import { clsx, type ClassValue } from "clsx";
import { extendTailwindMerge } from "tailwind-merge";

// 皮肤 utility(style.css 的 @utility)要登记成各自独立的类组:
// tailwind-merge 默认把 `accent-*` 全当成 accent-color 工具类,
// `cn("accent-gradient accent-glow")` 会只留后一个,渐变底色悄悄丢失。
const twMerge = extendTailwindMerge<
  "tk-accent-gradient" | "tk-accent-glow" | "tk-accent-soft" | "tk-accent-fg" | "tk-text-gradient" | "tk-display"
>({
  extend: {
    classGroups: {
      "tk-accent-gradient": ["accent-gradient"],
      "tk-accent-glow": ["accent-glow"],
      "tk-accent-soft": ["accent-soft"],
      "tk-accent-fg": ["accent-fg"],
      "tk-text-gradient": ["text-gradient"],
      "tk-display": ["tk-display"],
    },
  },
});

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
