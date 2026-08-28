#pragma once

// 讲解类提示词（AI 自测、AI 讲解、讲解差异）共用的风格提示：贴近主流
// 中文 C++ 教程的讲法和术语习惯，不生造术语。这里不是真的联网抓取这些
// 站点内容——AiService 没有搜索/浏览能力，只是提示模型往这个方向组织
// 语言，权当术语和讲法的锚点。
inline constexpr const char* kChineseTutorialStyleHint =
    "讲解风格和术语尽量贴近菜鸟教程、C语言中文网、微软 Learn 中文文档、"
    "w3cschool 这类主流中文 C++ 教程的习惯讲法，不要生造术语。";
