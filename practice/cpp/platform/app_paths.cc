#include "app_paths.h"

#include <glib.h>
#include <glib/gstdio.h>
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

string released_data_dir() {
    const string base = Glib::get_user_data_dir();
    const string current = Glib::build_filename(base, "athena-cpp");
    const string legacy = Glib::build_filename(base, "Athena");
    const bool current_exists =
        Glib::file_test(current, Glib::FileTest::EXISTS);
    const bool legacy_exists =
        Glib::file_test(legacy, Glib::FileTest::EXISTS);
    if (!current_exists && legacy_exists &&
        g_rename(legacy.c_str(), current.c_str()) != 0) {
        return legacy;
    }
    return current;
}
