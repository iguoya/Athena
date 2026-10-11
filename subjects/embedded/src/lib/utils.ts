import { clsx, type ClassValue } from "clsx";
import { extendTailwindMerge } from "tailwind-merge";

// 皮肤 utility(style.css 里的纯 CSS 类)登记成各自独立的类组:
// tailwind-merge 默认把 `accent-*` 全当成 accent-color 工具类,
// `cn("accent-gradient accent-soft")` 会只留后一个,渐变底色悄悄丢失。
// `tk-*` 与 `text-gradient` 同理,免得被当成 text-color / 字号误合并。
const twMerge = extendTailwindMerge<
  | "tk-accent-gradient"
  | "tk-accent-soft"
  | "tk-accent-fg"
  | "tk-text-gradient"
  | "tk-card"
  | "tk-card-hover"
  | "tk-display"
>({
  extend: {
    classGroups: {
      "tk-accent-gradient": ["accent-gradient"],
      "tk-accent-soft": ["accent-soft"],
      "tk-accent-fg": ["accent-fg"],
      "tk-text-gradient": ["text-gradient"],
      "tk-card": ["tk-card"],
      "tk-card-hover": ["tk-card-hover"],
      "tk-display": ["tk-display"],
    },
  },
});

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
