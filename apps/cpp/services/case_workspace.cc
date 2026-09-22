#include "services/case_workspace.h"

#include "platform/app_paths.h"

#include <giomm/resource.h>
#include <glibmm/fileutils.h>
#include <glibmm/miscutils.h>

#include <algorithm>
#include <stdexcept>
#include <utility>

using namespace std;

namespace {

constexpr const char* kResourcePrefix = "/app/cases/";

string case_resource_dir(const string& case_id) {
    return string(kResourcePrefix) + case_id;
}

// 案例目录名由生成器校验过（[a-z0-9_]），运行期再挡一道：这个值会拼进
// 文件路径和 GResource 路径，catalog 万一被改坏不能让它穿出目录去。
void reject_unsafe_case_id(const string& case_id) {
    const bool ok = !case_id.empty() &&
        all_of(case_id.begin(), case_id.end(), [](unsigned char ch) {
            return (ch >= 'a' && ch <= 'z') || (ch >= '0' && ch <= '9') || ch == '_';
        });
    if (!ok) {
        throw runtime_error("unsafe case id: " + case_id);
    }
}

// 同理约束文件名：只认骨架里出现过的名字，调用方负责比对，这里只挡分隔符。
void reject_unsafe_file_name(const string& name) {
    if (name.empty() || name.find('/') != string::npos ||
        name.find('\\') != string::npos || name.find("..") != string::npos) {
        throw runtime_error("unsafe case file name: " + name);
    }
}

}  // namespace

vector<CaseFile> read_skeleton_from_resources(const string& case_id) {
    reject_unsafe_case_id(case_id);
    const string dir = case_resource_dir(case_id);

    vector<string> names;
    try {
        names = Gio::Resource::enumerate_children_global(
            dir + "/", Gio::Resource::LookupFlags::NONE);
    } catch (const Glib::Error& error) {
        throw runtime_error(
            "case " + case_id + " is not in GResource: " + error.what());
    }
    sort(names.begin(), names.end());

    vector<CaseFile> files;
    for (const string& name : names) {
        // 案例目录是平的；真出现子目录时跳过而不是崩，生成器那边也只收文件。
        if (!name.empty() && name.back() == '/') {
            continue;
        }
        const Glib::RefPtr<const Glib::Bytes> bytes =
            Gio::Resource::lookup_data_global(dir + "/" + name);
        gsize size = 0;
        const auto* data = static_cast<const char*>(bytes->get_data(size));
        files.push_back(CaseFile{
            .name = name,
            .contents = string(data, size),
        });
    }
    if (files.empty()) {
        throw runtime_error("case " + case_id + " has no files in GResource");
    }
    return files;
}

CaseWorkspace::CaseWorkspace(string root, SkeletonReader reader)
    : m_root(std::move(root)),
      m_reader(reader ? std::move(reader) : SkeletonReader(read_skeleton_from_resources)) {}

string CaseWorkspace::default_root() {
    return Glib::build_filename(released_data_dir(), "cases");
}

string CaseWorkspace::directory_of(const string& case_id) const {
    reject_unsafe_case_id(case_id);
    return Glib::build_filename(m_root, case_id);
}

vector<CaseFile> CaseWorkspace::skeleton_of(const string& case_id) const {
    vector<CaseFile> skeleton = m_reader(case_id);
    if (skeleton.empty()) {
        throw runtime_error("case " + case_id + " has an empty skeleton");
    }
    return skeleton;
}

vector<CaseFile> CaseWorkspace::ensure(const string& case_id) const {
    const string dir = directory_of(case_id);
    if (g_mkdir_with_parents(dir.c_str(), 0700) != 0) {
        throw runtime_error("cannot create case workspace: " + dir);
    }

    vector<CaseFile> current;
    for (const CaseFile& file : skeleton_of(case_id)) {
        const string path = Glib::build_filename(dir, file.name);
        // 缺一个补一个：学员删掉某个文件时不必整个重置。已经在的不动，
        // 那是他的编辑。
        if (!Glib::file_test(path, Glib::FileTest::EXISTS)) {
            Glib::file_set_contents(path, file.contents);
            current.push_back(file);
            continue;
        }
        current.push_back(CaseFile{
            .name = file.name,
            .contents = Glib::file_get_contents(path),
        });
    }
    return current;
}

vector<CaseFile> CaseWorkspace::reset(const string& case_id) const {
    const string dir = directory_of(case_id);
    if (g_mkdir_with_parents(dir.c_str(), 0700) != 0) {
        throw runtime_error("cannot create case workspace: " + dir);
    }
    vector<CaseFile> skeleton = skeleton_of(case_id);
    for (const CaseFile& file : skeleton) {
        Glib::file_set_contents(Glib::build_filename(dir, file.name), file.contents);
    }
    return skeleton;
}

void CaseWorkspace::save(
    const string& case_id, const string& file, const string& contents) const {
    reject_unsafe_file_name(file);
    const vector<CaseFile> skeleton = skeleton_of(case_id);
    const bool known = any_of(
        skeleton.begin(), skeleton.end(),
        [&file](const CaseFile& entry) { return entry.name == file; });
    if (!known) {
        throw runtime_error("case " + case_id + " has no file named " + file);
    }
    const string dir = directory_of(case_id);
    if (g_mkdir_with_parents(dir.c_str(), 0700) != 0) {
        throw runtime_error("cannot create case workspace: " + dir);
    }
    Glib::file_set_contents(Glib::build_filename(dir, file), contents);
}

bool CaseWorkspace::modified(const string& case_id) const {
    const string dir = directory_of(case_id);
    for (const CaseFile& file : skeleton_of(case_id)) {
        const string path = Glib::build_filename(dir, file.name);
        if (!Glib::file_test(path, Glib::FileTest::EXISTS)) {
            // 还没展开过不算改过；展开后被删掉才算。
            return Glib::file_test(dir, Glib::FileTest::IS_DIR);
        }
        if (Glib::file_get_contents(path) != file.contents) {
            return true;
        }
    }
    return false;
}
