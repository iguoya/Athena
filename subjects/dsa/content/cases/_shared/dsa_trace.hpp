// 实验步进可视化协议（本应用 ADR 0004）。
// 驱动代码用本头向 stdout 打印 `#dsa-trace {...}` 的状态快照行，前端回放器
// 按前缀抽帧逐步渲染。不 include 本头 = 零成本；include 了不用也无输出。
// 本头不绑定案例的结点类型：只收值数组与下标，遍历取样由调用方完成
// （驱动代码本来就有 print 遍历）。
#pragma once

#include <cstdio>
#include <iostream>
#include <string>
#include <string_view>

namespace dsa_trace {

// JSON 字符串转义。note 里有引号/反斜杠时不能裸拼；控制字符转 \u00XX，
// 保证一行里没有裸控制字符、行结构不被破坏。UTF-8 多字节落在默认分支原样通过。
inline std::string json_string(std::string_view s) {
    std::string out = "\"";
    for (char c : s) {
        switch (c) {
            case '"': out += "\\\""; break;
            case '\\': out += "\\\\"; break;
            case '\n': out += "\\n"; break;
            case '\r': out += "\\r"; break;
            case '\t': out += "\\t"; break;
            default:
                if (static_cast<unsigned char>(c) < 0x20) {
                    char buf[8];
                    std::snprintf(buf, sizeof buf, "\\u%04x",
                                  static_cast<unsigned char>(c));
                    out += buf;
                } else {
                    out += c;
                }
        }
    }
    out += '"';
    return out;
}

// 链表快照：values 按从头结点遍历的顺序取样，接受 initializer_list、
// vector 等任何可遍历的 int 序列——帧必须是真实状态，不是预期的剧本；
// focus 是当前步骤关注的结点下标（-1 无焦点）。head 不进协议：快照约定
// 从头取样，头下标恒冗余。
template <class Seq>
void list(int step, std::string_view note, const Seq& values, int focus) {
    std::string js = "#dsa-trace {\"kind\":\"list\",\"step\":";
    js += std::to_string(step);
    js += ",\"note\":";
    js += json_string(note);
    js += ",\"focus\":";
    js += std::to_string(focus);
    js += ",\"values\":[";
    bool first = true;
    for (int v : values) {
        if (!first) js += ',';
        first = false;
        js += std::to_string(v);
    }
    js += "]}\n";
    std::cout << js;
}

} // namespace dsa_trace
