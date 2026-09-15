#include "app_paths.h"

#include <glibmm.h>

#include <cstdlib>

namespace {

string directory_from_environment(const char* name) {
    const char* value = getenv(name);
    if (value == nullptr) {
        return {};
    }
    const string path(value);
    return Glib::file_test(path, Glib::FileTest::IS_DIR) ? path : string{};
}

} // namespace

string external_apps_root() {
    return directory_from_environment("ATHENA_APPS_ROOT");
}

string own_app_root() {
    return directory_from_environment("ATHENA_CPP_ROOT");
}
