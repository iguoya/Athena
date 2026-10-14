// KaTeX 的自定义宏表。Octave 手册里 @tex 块与 @math 的公式转成标准 LaTeX，目前不需要自定义宏；
// 新增宏时由 scripts/check-math.mjs 报出「未知命令」。
export const MACROS: Record<string, string> = {};
