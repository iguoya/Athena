import { useEffect, useState } from "react";
import { useApp } from "@/state/store";

/** 抽屉的像素宽度：收窄时固定 480，展开时占窗口的大半。画布要据此扣掉被盖住的部分。 */
export function useDrawerWidth(): number {
  const wide = useApp((s) => s.drawerWide);
  const [width, setWidth] = useState(() => window.innerWidth);
  useEffect(() => {
    const onResize = () => setWidth(window.innerWidth);
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);
  return wide ? Math.round(Math.min(920, width * 0.72)) : Math.min(480, Math.round(width * 0.9));
}
