import { isTauri } from "@tauri-apps/api/core";
import { openUrl } from "@tauri-apps/plugin-opener";

/** 出处链接在系统浏览器里打开核对；webview 里直接导航会把应用带走。开发模式（浏览器）退回 window.open。 */
export async function openExternal(url: string): Promise<void> {
  if (isTauri()) {
    await openUrl(url);
  } else {
    window.open(url, "_blank", "noopener");
  }
}
