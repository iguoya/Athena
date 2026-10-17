import { useMemo, useState } from "react";
import type { BayInfo, Snapshot } from "../types";
import {
  KINDS,
  actionsByMember,
  membersOf,
  type Action,
  type AgentColor,
  type KindId,
} from "../activity";

// 成员视图：一人一栏，栏内按行为类型分组（发布 / 验收 / 返工 / 开工 / 交付 / 消息 …），
// 每组折叠显示最近几条。回答「这个智能体都干了什么」，不再把所有人的动作混在一条流里。
const PREVIEW = 3;

export default function MemberView({
  snap,
  bay,
  bayInfo,
  colorOf,
  onOpenTask,
}: {
  snap: Snapshot;
  bay: string;
  bayInfo?: BayInfo;
  colorOf: (name: string) => AgentColor;
  onOpenTask: (tid: string) => void;
}) {
  const leader = bayInfo?.leader ?? "";
  const members = useMemo(() => membersOf(snap, bay, bayInfo), [snap, bay, bayInfo]);
  const byMember = useMemo(() => actionsByMember(snap, bay, leader), [snap, bay, leader]);
  const [open, setOpen] = useState<Record<string, boolean>>({});

  if (members.length === 0) {
    return <div className="flex h-full items-center justify-center text-ink-500">这个舱还没有成员</div>;
  }

  return (
    <div className="flex h-full gap-4 overflow-x-auto p-5">
      {members.map((name) => {
        const c = colorOf(name);
        const all = byMember.get(name) ?? [];
        const byKind = new Map<KindId, Action[]>();
        for (const a of all) byKind.set(a.kind, [...(byKind.get(a.kind) ?? []), a]);
        return (
          <div
            key={name}
            className="flex w-80 shrink-0 flex-col overflow-hidden rounded-2xl border border-line bg-white"
          >
            <div className={"px-4 py-3 " + c.soft}>
              <div className="flex items-center gap-2">
                <span className={"inline-block h-3 w-3 rounded-full " + c.dot} />
                <span className="text-base font-bold">{name}</span>
                <span className="text-xs text-ink-500">{name === leader ? "leader" : "worker"}</span>
                <span className="ml-auto text-xs text-ink-500">共 {all.length} 条</span>
              </div>
            </div>
            <div className="min-h-0 flex-1 overflow-y-auto p-3">
              {KINDS.map((k) => {
                const list = byKind.get(k.id) ?? [];
                if (list.length === 0) return null;
                const key = `${name}/${k.id}`;
                const expanded = !!open[key];
                const shown = expanded ? list : list.slice(0, PREVIEW);
                return (
                  <div key={k.id} className="mb-4">
                    <div className="mb-1.5 flex items-center gap-2">
                      <span className={"rounded px-1.5 py-0.5 text-xs font-medium " + k.tone}>
                        {k.label}
                      </span>
                      <span className="text-xs text-ink-300">{list.length}</span>
                      {list.length > PREVIEW && (
                        <button
                          className="ml-auto text-xs text-brand-700"
                          onClick={() => setOpen((s) => ({ ...s, [key]: !expanded }))}
                        >
                          {expanded ? "收起" : `展开全部 ${list.length}`}
                        </button>
                      )}
                    </div>
                    <ul className="space-y-1.5">
                      {shown.map((a, i) => (
                        <li
                          key={i}
                          className={
                            "rounded-lg border-l-4 bg-paper px-2.5 py-1.5 text-sm " + c.border
                          }
                        >
                          <div className="flex items-center gap-2 text-xs text-ink-500">
                            {a.tid !== "" && (
                              <button
                                className="font-mono text-brand-700 hover:underline"
                                onClick={() => onOpenTask(a.tid)}
                              >
                                {a.tid}
                              </button>
                            )}
                            {a.to && a.to !== "all" && <span>→ {a.to}</span>}
                            <span className="ml-auto text-ink-300">{a.at}</span>
                          </div>
                          <div className="mt-0.5 line-clamp-2 leading-snug">{a.title}</div>
                          {a.detail !== "" && k.id !== "msg" && (
                            <div className="mt-0.5 line-clamp-2 text-xs text-ink-500">{a.detail}</div>
                          )}
                        </li>
                      ))}
                    </ul>
                  </div>
                );
              })}
              {all.length === 0 && <div className="py-6 text-center text-xs text-ink-300">还没有行为记录</div>}
            </div>
          </div>
        );
      })}
    </div>
  );
}
