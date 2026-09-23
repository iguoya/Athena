function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function inline(text: string): string {
  const escaped = escapeHtml(text);
  return escaped
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>");
}

/** 短文用的最小 Markdown：标题、段落、粗斜体。不做 HTML 直通。 */
export function renderMarkdown(source: string): string {
  const lines = source.replace(/\r\n/g, "\n").split("\n");
  const out: string[] = [];
  let para: string[] = [];

  const flush = () => {
    if (para.length === 0) {
      return;
    }
    out.push(`<p>${inline(para.join(" "))}</p>`);
    para = [];
  };

  for (const raw of lines) {
    const line = raw.trimEnd();
    if (line.trim() === "") {
      flush();
      continue;
    }
    const heading = /^(#{1,3})\s+(.+)$/.exec(line.trim());
    if (heading) {
      flush();
      const marks = heading[1] ?? "#";
      const title = heading[2] ?? "";
      const level = marks.length;
      out.push(`<h${level}>${inline(title)}</h${level}>`);
      continue;
    }
    para.push(line.trim());
  }
  flush();
  return out.join("");
}
