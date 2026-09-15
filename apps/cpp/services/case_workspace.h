#pragma once

#include <functional>
#include <string>
#include <vector>

using namespace std;

// 骨架案例的工作副本（ADR 0053）。
//
// 骨架原件随 GResource 分发，只读；学员改的是用户数据目录下的副本。分成两份
// 是因为两条约束要同时满足：教学内容只能从 GResource 读（AGENTS.md——运行期
// 按文件路径找随程序分发的东西，装到别的机器上就失效），而实验又必须可编辑。
// 于是仓库里的案例任何时候都不被应用改写，「重置」就是删掉副本重新展开。
struct CaseFile {
    // 相对案例目录的文件名，例如 main.cpp。
    string name;
    string contents;
};

// 读骨架原件的方式。默认实现读 GResource；测试注入自己的，免得为了测试
// 往 GResource 里塞案例。
using SkeletonReader = function<vector<CaseFile>(const string& case_id)>;

// 从 GResource 的 /app/cases/<case_id>/ 读出骨架原件，按文件名排序。
// 案例不存在或为空时抛 runtime_error。
vector<CaseFile> read_skeleton_from_resources(const string& case_id);

class CaseWorkspace final {
public:
    // root 是工作副本的根目录；reader 缺省时读 GResource。
    explicit CaseWorkspace(string root, SkeletonReader reader = {});

    // Glib::get_user_data_dir()/Athena/cases —— 与学习库同一个 Athena 目录下。
    static string default_root();

    // 这个案例的工作副本目录，不保证存在。
    string directory_of(const string& case_id) const;

    // 确保工作副本可用：目录或文件缺失就按骨架补齐，已有的编辑保持不动。
    // 返回副本当前内容。
    vector<CaseFile> ensure(const string& case_id) const;

    // 丢弃全部编辑，按骨架重新展开。
    vector<CaseFile> reset(const string& case_id) const;

    // 保存一个文件。file 必须是该案例骨架里已有的文件名——学员改的是骨架
    // 里的文件，不新增，这样驱动和编译命令都不必随副本变化。
    void save(const string& case_id, const string& file, const string& contents) const;

    // 副本内容是否已经偏离骨架。界面据此决定「重置」要不要可点。
    bool modified(const string& case_id) const;

private:
    vector<CaseFile> skeleton_of(const string& case_id) const;

    string m_root;
    SkeletonReader m_reader;
};
