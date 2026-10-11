// 主窗口可见性：托盘常驻时前端整体挂起的开关（隐藏即停轮询、停 3D 帧循环）。
// 初始状态主动问一次后端（开机自启拉起时窗口从未显示，靠这查问到「隐藏」），
// 此后的变化走 resident 发的 launcher://visibility 事件。

import { useEffect, useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";

export function useWindowVisible(): boolean {
  const [visible, setVisible] = useState(true);
  useEffect(() => {
    let alive = true;
    invoke<boolean>("main_window_visible")
      .then((v) => {
        if (alive) setVisible(v);
      })
      .catch(() => {});
    const unlisten = listen<boolean>("launcher://visibility", (e) => {
      if (alive) setVisible(e.payload);
    });
    return () => {
      alive = false;
      unlisten.then((f) => f());
    };
  }, []);
  return visible;
}
