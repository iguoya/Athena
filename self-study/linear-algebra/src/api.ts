import { invoke as tauriInvoke } from "@tauri-apps/api/core";

export function hasTauri(): boolean {
  return (
    typeof window !== "undefined" &&
    !!(window as Window & { __TAURI_INTERNALS__?: unknown }).__TAURI_INTERNALS__
  );
}

/** 非 Tauri 环境（纯浏览器预览）下调用壳命令会抛出带指引的错误。 */
export async function invoke<T>(cmd: string, args?: Record<string, unknown>): Promise<T> {
  if (!hasTauri()) {
    throw new Error("当前不在应用窗口里（缺少 Tauri）。请用 `pnpm run tauri:dev` 启动。");
  }
  return tauriInvoke<T>(cmd, args);
}
