import { isTauri } from "@tauri-apps/api/core";
import { getCurrentWindow } from "@tauri-apps/api/window";
import { Minus, Square, X } from "lucide-react";

// Custom title bar: the native one is turned off in tauri.conf.json so the skins reach the window edge.
export function TitleBar() {
  if (!isTauri()) return null;
  const win = getCurrentWindow();
  const btn = "grid h-9 w-11 place-items-center text-muted transition-colors hover:bg-surface-strong hover:text-fg";
  return (
    <div data-tauri-drag-region className="fixed inset-x-0 top-0 z-50 flex h-9 items-center justify-end">
      <button type="button" aria-label="最小化" className={btn} onClick={() => win.minimize()}>
        <Minus size={15} />
      </button>
      <button type="button" aria-label="最大化" className={btn} onClick={() => win.toggleMaximize()}>
        <Square size={12} />
      </button>
      <button
        type="button"
        aria-label="关闭"
        className={`${btn} hover:!bg-[#e5484d] hover:!text-white`}
        onClick={() => win.close()}
      >
        <X size={16} />
      </button>
    </div>
  );
}
