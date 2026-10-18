# T-003 交付说明

47 段空 `zh` 的 para/listitem 都写在 `comms/gtkmm-demo/artifacts/cursor/appendix-g.json`。键是节 id，内层键是该节 `blocks` 下标（字符串）。没有改 `guide/gtkmm/`。

自检：空段与草稿一一对应（defs 3、hg 40、problems 4）；原文反引号片段在译文里出现次数不少于原文；Markdown 链接的 url 原样保留；用 `glossary.json` 的 `avoid` 扫过，0 处违例。`widget` 用「部件」，`signal handler` 用「信号处理函数」。预处理宏没有写成「预处理器」，避开「处理器」这条禁用词。

类型对照表 6 行（块 280–285 中的类型名，以及块 280–284 整行）没有中文可译，按原文保留；表头译成「C 类型 → C++ 类型」，最后一行括号里的「文件名则用 std::string」已译。

## 不确定（2）

1. `sec-wrapping-hg-files` 块 83，标记是 `errthrow`，正文却写 C 的 `*_new()` 末尾 `GError**`「should be ignored」。按正文译成「应被忽略」。同文件块 179 的 `errthrow` 才是「用来抛出异常」，两处没有强行统一。
2. `sec-wrapping-defs-files` 块 12，「described in the Documentation section」语法上紧挨 `*_docs.xml`，译文挂在这个文件上。若要修饰脚本生成的全部产物，合并时改「后者」即可。

## 按原文保留、没有改写成更顺的说法

- 块 128 的 none / shallow / deep 是 m4 所有权记号，留英文。
- 块 269 正文写从 `const char**` 设置 `Glib::ustring&`，紧接着的代码示例是 `const char*`。译文跟正文，没有改成跟代码一致。
- 块 267「the value returned」按后一句理解：放进 `out_mime_type` 的是 C 输出参数带回的值。这条 C 函数本身还返回 `GInputStream*`，译文没有把它说成函数返回值。
- `sec-wrapping-problems` 块 13 的 hooks 译成「钩子」。
- 块 7「or this:」是承接上一句编译错误的片段，译成「或者是这样：」。上一句已有译文「菜单如下所示」与原文不符，这次没有动。

## 看见但没有改的已有译文

`sec-wrapping-defs-files` 块 31 原文是「`mmgir` 可以生成全部 `.defs` 文件」，现有 `zh` 是「告诉 gmmproc 在生成的文件中包含 private/button_p.h 头文件」。这是别处句子，与本段无关。任务书只补空 `zh`，所以留着。
