import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { isTauri } from "@tauri-apps/api/core";
import { check } from "@tauri-apps/plugin-updater";
import { relaunch } from "@tauri-apps/plugin-process";
import { Sparkles } from "lucide-react";

type State = { version: string; percent: number } | null;

// On launch, look for a newer release; if there is one, install it quietly and restart (ADR 0018).
// Offline or failed checks are ignored: the app must work without the network (ADR 0002).
export function UpdateToast() {
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

  return (
    <AnimatePresence>
      {state && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 20 }}
          className="glass fixed bottom-6 right-6 z-50 w-72 p-4"
        >
          <p className="flex items-center gap-2 text-sm font-medium">
            <Sparkles size={16} className="text-accent" />
            摘星有新版本 {state.version}，正在更新
          </p>
          <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-line">
            <motion.div
              className="h-full rounded-full bg-[linear-gradient(90deg,var(--accent),var(--accent-2))]"
              animate={{ width: `${state.percent}%` }}
            />
          </div>
          <p className="mt-2 text-xs text-muted">更新完会自动重新打开，学习记录不受影响。</p>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
