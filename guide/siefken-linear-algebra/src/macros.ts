// 上游 book/common/preamble.tex 里的数学宏，翻成 KaTeX 的 macros 表。
// 只收书里实际用到的；新增宏时由 scripts/check-math.mjs 报出「未知命令」。
export const MACROS: Record<string, string> = {
  "\\Span": "\\operatorname{span}", "\\Img": "\\operatorname{img}", "\\Id": "\\operatorname{id}", "\\Ident": "\\operatorname{id}",
  "\\Vol": "\\operatorname{Vol}", "\\VolChange": "\\operatorname{Vol\\,Change}", "\\Range": "\\operatorname{range}",
  "\\Rref": "\\operatorname{rref}", "\\rref": "\\operatorname{rref}", "\\Rank": "\\operatorname{rank}",
  "\\Comp": "\\operatorname{v\\,comp}", "\\Vcomp": "\\operatorname{v\\,comp}", "\\Null": "\\operatorname{null}",
  "\\Nullity": "\\operatorname{nullity}", "\\Char": "\\operatorname{char}", "\\chr": "\\operatorname{char}", "\\Proj": "\\operatorname{proj}",
  "\\proj": "\\operatorname{proj}", "\\Dim": "\\operatorname{dim}", "\\Perp": "\\operatorname{perp}",
  "\\Ker": "\\operatorname{kernel}", "\\Row": "\\operatorname{row}", "\\Col": "\\operatorname{col}", "\\Rep": "\\operatorname{Rep}",
  "\\BasisChange": "[#2\\!\\leftarrow\\!#1]",
  "\\xhat": "{\\vec e_1}", "\\yhat": "{\\vec e_2}", "\\zhat": "{\\vec e_3}", "\\sbasis": "\\vec{e}_{#1}",
  "\\mat": "\\begin{bmatrix}#1\\end{bmatrix}", "\\matc": "\\begin{bmatrix}#1\\end{bmatrix}",
  "\\formarg": "\\big(#1;\\, #2\\big)",
  "\\abs": "\\left\\lvert #1\\right\\rvert", "\\Abs": "\\left\\lvert #1\\right\\rvert",
  "\\norm": "\\left\\lVert #1\\right\\rVert", "\\Norm": "\\left\\lVert #1\\right\\rVert",
  "\\Set": "\\left\\{#1\\right\\}", "\\given": "\\,\\middle|\\,",
  "\\Rrefto": "\\xrightarrow{\\text{row reduces to}}", "\\hdash": "\\text{-------}", "\\bigmathstrut": "\\vphantom{\\Big(}",
  "\\R": "\\mathbb{R}", "\\C": "\\mathbb{C}", "\\N": "\\mathbb{N}", "\\Z": "\\mathbb{Z}", "\\Q": "\\mathbb{Q}",
  "\\th": "^{\\text{th}}",
};
