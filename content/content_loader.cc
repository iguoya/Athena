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
    if (file) {
        ostringstream content;
        content << file.rdbuf();
        return content.str();
    }

    return load_resource("/app/sources/" + relative_path);
}

