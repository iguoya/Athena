import { create } from "zustand";
import { persist } from "zustand/middleware";

export const SKINS = [
  { id: "dawn", name: "晨光", hint: "柔和渐变" },
  { id: "night", name: "极光", hint: "夜间霓虹" },
  { id: "journal", name: "手账", hint: "纸张贴纸" },
] as const;

export type SkinId = (typeof SKINS)[number]["id"];

type SkinState = {
  skin: SkinId;
  setSkin: (skin: SkinId) => void;
};

// The skin choice is a per-device preference, so localStorage is enough; progress lives in SQLite.
export const useSkin = create<SkinState>()(
  persist(
    (set) => ({
      skin: "dawn",
      setSkin: (skin) => set({ skin }),
    }),
    { name: "lumi-skin" },
  ),
);

export function applySkin(skin: SkinId) {
  document.documentElement.dataset.style = skin;
}
