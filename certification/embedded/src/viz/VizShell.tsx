// viz 块的公共外壳:控制区在顶部,内容在下。
// title 只作为悬停提示(沿用 Vue 版的行为:title 落在根节点上,不渲染成可见标题)。
import type { ReactNode } from "react";

export default function VizShell({
  title,
  controls,
  children,
}: {
  title?: string;
  controls?: ReactNode;
  children: ReactNode;
}) {
  return (
    <div className="p-5" title={title}>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <span className="accent-fg text-sm font-bold" />
        <div className="flex flex-wrap items-center gap-3 text-[13px]">{controls}</div>
      </div>
      {children}
    </div>
  );
}
