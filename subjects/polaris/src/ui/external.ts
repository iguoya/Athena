// 出处链接在系统浏览器里打开。Tauri 里走 opener 插件；纯浏览器预览（vite dev）里退回 window.open。
export async function openExternal(url: string): Promise<void> {
  try {
    const { openUrl } = await import("@tauri-apps/plugin-opener");
    await openUrl(url);
  } catch {
    window.open(url, "_blank", "noopener,noreferrer");
  }
}
