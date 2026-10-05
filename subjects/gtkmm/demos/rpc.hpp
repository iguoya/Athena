// JSON-RPC 2.0 over stdio（NDJSON 行分隔）：壳与演示进程之间的协议
// （应用 ADR 0001 决策 5）。上行 stdout、下行 stdin、日志走 stderr。
#pragma once

#include <gtkmm.h>

#include <cstdio>
#include <functional>
#include <sstream>
#include <string>

namespace rpc {

/// 发一条通知（无 id）。GTK 主循环内随时可调；行缓冲按行 flush。
inline void notify(const std::string& method, const Glib::ustring& params_json) {
    std::ostringstream out;
    out << "{\"jsonrpc\":\"2.0\",\"method\":\"" << method << "\",\"params\":" << params_json << "}\n";
    std::fputs(out.str().c_str(), stdout);
    std::fflush(stdout);
}

/// 上报一次控件信号（文档联动与观察题的事件源）。
inline void signal(const std::string& widget, const std::string& signal_name,
                   const std::string& detail = "") {
    std::string params = "{\"widget\":\"" + widget + "\",\"signal\":\"" + signal_name + "\"";
    if (!detail.empty()) {
        params += ",\"detail\":\"" + detail + "\"";
    }
    params += "}";
    notify("signal", params);
}

/// 监听下行请求，交给 handler(jsonrpc_id, method)。返回的连接由调用方持住。
/// 用 Glib 的 IO watch 而不是阻塞读：GTK 主循环不能被 stdin 卡住。
inline sigc::connection watch_requests(
    std::function<void(const std::string& id, const std::string& method)> handler) {
    Glib::RefPtr<Glib::IOChannel> channel = Glib::IOChannel::create_from_fd(0);
    return Glib::signal_io().connect(
        [channel, handler](Glib::IOCondition condition) {
            if ((condition & Glib::IOCondition::IO_IN) == Glib::IOCondition()) return false;
            Glib::ustring line;
            try {
                channel->read_line(line);
            } catch (const Glib::Error&) {
                return false;
            }
            // 只解析壳会发的三种请求；行尾带 \n，Glib::ustring 截掉。
            const std::string text = line.raw();
            const auto extract = [&text](const char* key) -> std::string {
                const std::string needle = std::string("\"") + key + "\":\"";
                const auto begin = text.find(needle);
                if (begin == std::string::npos) return "";
                const auto start = begin + needle.size();
                const auto end = text.find('"', start);
                return end == std::string::npos ? "" : text.substr(start, end - start);
            };
            handler(extract("id"), extract("method"));
            return true;
        },
        channel,
        Glib::IOCondition::IO_IN);
}

inline void respond(const std::string& id, const std::string& result_json) {
    std::ostringstream out;
    out << "{\"jsonrpc\":\"2.0\",\"id\":" << (id.empty() ? "null" : id)
        << ",\"result\":" << result_json << "}\n";
    std::fputs(out.str().c_str(), stdout);
    std::fflush(stdout);
}

}  // namespace rpc
