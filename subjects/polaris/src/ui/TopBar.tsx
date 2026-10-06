import { Check } from "lucide-react";
import type { Catalog } from "@/content/catalog";
import { THEMES, useApp } from "@/state/store";
import iconUrl from "../../icon.svg";

interface Props {
  catalog: Catalog;
}

export function TopBar({ catalog }: Props) {
  const loc = useApp((s) => s.loc);
  const go = useApp((s) => s.go);
  const theme = useApp((s) => s.theme);
  const setTheme = useApp((s) => s.setTheme);
  const inBase = loc.view === "base";

  const tab = (active: boolean) =>
    `rounded-lg px-3.5 py-1.5 text-[13.5px] font-medium transition-colors ${active ? "bg-ink text-[color:var(--bg)]" : "text-muted hover:bg-surface-2 hover:text-ink"}`;

  return (
    <header className="relative z-40 flex h-14 shrink-0 items-center gap-6 border-b border-line bg-surface/85 px-5 backdrop-blur">
      <button type="button" onClick={() => go({ view: "home" })} className="flex items-center gap-2.5" aria-label="回到总览">
        <img src={iconUrl} alt="" className="size-7" draggable={false} />
        <span className="text-[17px] font-bold tracking-tight">北极星</span>
        <span className="hidden text-[12px] text-faint md:inline">路线图与指南针</span>
      </button>

      <nav className="flex items-center gap-1" aria-label="主导航">
        <button type="button" className={tab(!inBase)} aria-current={!inBase ? "page" : undefined} onClick={() => go({ view: "home" })}>
          路线
        </button>
        <button
          type="button"
          className={tab(inBase)}
          aria-current={inBase ? "page" : undefined}
          onClick={() => go({ view: "base", mapId: catalog.maps[0].id })}
        >
          底盘
        </button>
      </nav>

      <div className="ml-auto flex items-center gap-1 rounded-xl border border-line bg-surface-2/60 p-1" role="radiogroup" aria-label="主题">
        {THEMES.map((item) => (
          <button
            key={item.id}
            type="button"
            role="radio"
            aria-checked={theme === item.id}
            onClick={() => setTheme(item.id)}
            className={`flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-[12.5px] font-medium transition-colors ${theme === item.id ? "bg-surface text-ink shadow-[var(--shadow-card)]" : "text-muted hover:text-ink"}`}
          >
            <span className="relative size-3.5 overflow-hidden rounded-full border border-line" style={{ background: `linear-gradient(135deg, ${item.swatch[0]} 50%, ${item.swatch[1]} 50%)` }} />
            {item.label}
            {theme === item.id && <Check size={12} className="text-accent" />}
          </button>
        ))}
      </div>
    </header>
  );
}
