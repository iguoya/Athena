// 教材原文:OCR 转录的官方教材文本,按节组装(忠于原文,个别 OCR 形近字误差在
// 页头有提示)。构建期 glob 收集,新组装的原文文件即被带上。
const textModules = import.meta.glob<string>(
  "../../content/textbooks/*/sections/*.txt",
  { query: "?raw", import: "default", eager: true },
);

export function textbookTextOf(sectionId: string): string | null {
  const hit = Object.entries(textModules).find(([path]) =>
    path.endsWith(`/sections/${sectionId}.txt`),
  );
  return hit ? hit[1] : null;
}
