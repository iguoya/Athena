/** 对话时间线的排序与日期标题。口径见 comms/comms-console/docs/view-semantics.md。 */

const WEEK = ["星期日", "星期一", "星期二", "星期三", "星期四", "星期五", "星期六"];

/** 正式消息的文件名时间戳，或 chat 行首时间，都折成 14 位 YYYYMMDDHHMMSS。 */
export function stampOf(raw: string): string {
  return raw.replace(/\D/g, "").slice(0, 14).padEnd(14, "0");
}

export function dayHeading(stamp: string): string {
  const y = Number(stamp.slice(0, 4));
  const m = Number(stamp.slice(4, 6));
  const d = Number(stamp.slice(6, 8));
  const wd = WEEK[new Date(y, m - 1, d).getDay()];
  return `${m}月${d}日 ${wd}`;
}

export function dayKey(stamp: string): string {
  return stamp.slice(0, 8);
}
