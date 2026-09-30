import { NavLink } from "react-router";
import { NAV } from "./nav";
import { SKINS, useSkin } from "@/theme/skins";
import { cn } from "@/lib/utils";

export function Sidebar() {
  const { skin, setSkin } = useSkin();
  return (
    <aside className="flex w-56 flex-none flex-col gap-1 border-r border-line bg-surface px-4 pb-5 pt-11 backdrop-blur-xl">
      <div className="mx-2 mb-5 font-display text-[26px] font-semibold leading-none tracking-tight">
        Lumi<span className="text-accent">.</span>
      </div>
      <nav aria-label="主导航" className="flex flex-col gap-1">
        {NAV.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-2.5 rounded-xl px-3 py-2 text-sm text-muted transition-all hover:text-fg",
                isActive && "bg-surface-strong font-medium text-fg shadow-skin",
              )
            }
          >
            <Icon size={18} strokeWidth={2} />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="mt-auto flex flex-col gap-3 px-1">
        <div role="group" aria-label="切换皮肤" className="flex gap-1 rounded-full border border-line bg-surface p-1">
          {SKINS.map((s) => (
            <button
              key={s.id}
              type="button"
              title={s.hint}
              aria-pressed={skin === s.id}
              onClick={() => setSkin(s.id)}
              className={cn(
                "flex-1 rounded-full py-1 text-xs transition-colors",
                skin === s.id ? "bg-accent text-on-accent" : "text-muted hover:text-fg",
              )}
            >
              {s.name}
            </button>
          ))}
        </div>
        <p className="px-1 text-xs text-muted">第一章 · 夯实高中</p>
      </div>
    </aside>
  );
}
