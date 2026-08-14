#include "content_loader.h"

#include <gio/gio.h>

#include <fstream>
#include <sstream>
#include <string_view>
#include <utility>

ContentLoader::ContentLoader(string project_root)
    : m_project_root(std::move(project_root)) {}

string ContentLoader::load_resource(const string& resource_path) const {
    GError* error = nullptr;
    GBytes* bytes = g_resources_lookup_data(
        resource_path.c_str(),
        G_RESOURCE_LOOKUP_FLAGS_NONE,
        &error);
    if (!bytes) {
        if (error) {
            g_error_free(error);
        }
        return {};
    }

    gsize size = 0;
    const char* data = static_cast<const char*>(g_bytes_get_data(bytes, &size));
    string content(data, size);
    g_bytes_unref(bytes);
    return content;
}

string ContentLoader::load_project_file(const string& relative_path) const {
    if (relative_path.empty()) {
        return {};
    }

    ifstream file(m_project_root + "/" + relative_path);
    if (!file) {
        return {};
    }

    ostringstream content;
    content << file.rdbuf();
    return content.str();
}

string ContentLoader::load_document(const string& relative_path) const {
    constexpr string_view resources_prefix = "resources/";
    if (relative_path.rfind(resources_prefix, 0) == 0) {
        const string resource_path =
            "/app/" + relative_path.substr(resources_prefix.size());
        if (string content = load_resource(resource_path); !content.empty()) {
            return content;
        }
    }

    return load_project_file(relative_path);
}

string ContentLoader::document_base_directory(
    const string& relative_path) const {
    const size_t slash = relative_path.find_last_of('/');
    const string directory =
        slash == string::npos ? "" : relative_path.substr(0, slash);
    return m_project_root + "/" + directory;
}
