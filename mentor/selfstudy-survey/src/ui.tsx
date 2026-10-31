import { openUrl } from "@tauri-apps/plugin-opener";
import type { ReactNode } from "react";
import { isStale, LEVEL_LABEL, STATUS_LABEL } from "./data";
import type { OfferStatus, Verify } from "./types";

// 在 Tauri 里交给系统浏览器；在普通浏览器预览时退回新标签页。
export function open(url: string) {
  if ("__TAURI_INTERNALS__" in window) {
    void openUrl(url);
  } else {
    window.open(url, "_blank", "noopener");
  }
}

export function Link({ url, children }: { url: string; children: ReactNode }) {
  return (
    <a
      href={url}
      className="ext"
      onClick={(e) => {
        e.preventDefault();
        open(url);
      }}
    >
      {children}
    </a>
  );
}

// 核对徽标：级别 + 日期 + 来源链接。report/pending 在视觉上明显弱于 official/notice，
// 读者一眼能分出「有原文」和「只是线索」；超过一年的标「可能过期」。
export function VerifyBadge({ v }: { v: Verify }) {
  const stale = v.level !== "pending" && isStale(v.date);
  return (
    <span className={`vb vb-${v.level}`} title={v.note ?? ""}>
      {LEVEL_LABEL[v.level]}
      {v.date ? ` · ${v.date}` : ""}
      {stale ? " · 可能过期" : ""}
      {v.source ? (
        <>
          {" "}
          <Link url={v.source}>来源</Link>
        </>
      ) : null}
    </span>
  );
}

export function StatusChip({ s }: { s: OfferStatus }) {
  return <span className={`chip chip-${s}`}>{STATUS_LABEL[s]}</span>;
}

// 「还没有数据」的占位提示。这类提示都表示信息未确定（不是「没有」），统一加问号前缀，
// 与已核实条目（VerifyBadge 带来源链接）形成一眼可辨的对照。
export function Empty({ children }: { children: ReactNode }) {
  return <div className="empty">? {children}</div>;
}

export function Section({ title, hint, children }: { title: string; hint?: string; children: ReactNode }) {
  return (
    <section className="sec">
      <h3>
        {title}
        {hint ? <small>{hint}</small> : null}
      </h3>
      {children}
    </section>
  );
}
