import hljs from "highlight.js/lib/core";
import cpp from "highlight.js/lib/languages/cpp";

// 教程内容清一色 C++（节页官方源码块与知识点代码块全部如此），按需只注册 cpp，
// 避免整包引入；将来内容出现别的语言，在这里补一行注册即可，渲染端不动。
hljs.registerLanguage("cpp", cpp);

const escapePlain = (code: string) =>
  code.replace(/[&<>]/g, (ch) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" })[ch] as string);

/**
 * 统一的代码高亮入口：已注册语言返回高亮 HTML（hljs 已转义代码文本，可直接注入），
 * 未注册语言或解析失败回退转义纯文本——代码可读性永远优先于着色。
 */
export function highlightCode(code: string, lang?: string | null): string {
  if (lang && hljs.getLanguage(lang)) {
    try {
      return hljs.highlight(code, { language: lang }).value;
    } catch {
      // 语法解析意外失败时按纯文本呈现，不阻塞页面
    }
  }
  return escapePlain(code);
}
