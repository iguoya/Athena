import { useEffect, useState } from "react";
import { isTauri } from "@tauri-apps/api/core";
import { check } from "@tauri-apps/plugin-updater";
import { relaunch } from "@tauri-apps/plugin-process";

type State = { version: string; percent: number } | null;

// 应用启动时静默检查更新：发现新版本就下载安装，进度条提示，装完自动重启（ADR 0172，
// 模式同摘星 ADR 0018）。离线或检查失败一律静默：应用必须能离线使用。
// 不做「下次启动生效」：Windows 上 NSIS 安装器必须先结束运行中的应用，假装无感不如明示。
export function AppUpdate() {
  const [state, setState] = useState<State>(null);

  useEffect(() => {
    if (!isTauri() || import.meta.env.DEV) return;
    let cancelled = false;
    (async () => {
      try {
        const update = await check({ timeout: 15000 });
        if (!update || cancelled) return;
        setState({ version: update.version, percent: 0 });
        let total = 0;
        let received = 0;
        await update.downloadAndInstall((event) => {
          if (event.event === "Started") total = event.data.contentLength ?? 0;
          if (event.event === "Progress") {
            received += event.data.chunkLength;
            if (total) setState({ version: update.version, percent: Math.round((received / total) * 100) });
          }
        });
        await relaunch();
      } catch {
        setState(null);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  if (!state) return null;
  return (
    <div
      style={{
        position: "fixed",
        right: 24,
        bottom: 24,
        zIndex: 50,
        width: 288,
        padding: 16,
        borderRadius: 12,
        background: "rgba(30, 32, 38, 0.88)",
        color: "#f4f2ec",
        boxShadow: "0 8px 24px rgba(0, 0, 0, 0.25)",
        fontFamily: "inherit",
      }}
    >
      <p style={{ margin: 0, fontSize: 14, fontWeight: 600 }}>
        有新版本 {state.version}，正在更新
      </p>
      <div style={{ marginTop: 12, height: 6, borderRadius: 3, overflow: "hidden", background: "rgba(255,255,255,0.18)" }}>
        <div
          style={{
            width: `${state.percent}%`,
            height: "100%",
            borderRadius: 3,
            background: "linear-gradient(90deg, #7aa2f7, #9ece6a)",
            transition: "width 0.2s ease",
          }}
        />
      </div>
      <p style={{ margin: "8px 0 0", fontSize: 12, opacity: 0.72 }}>
        更新完会自动重新打开，学习记录不受影响。
      </p>
    </div>
  );
}

