#include "app_paths.h"

#include <glibmm.h>

#include <cstdlib>

string external_apps_root() {
    const char* value = getenv("ATHENA_APPS_ROOT");
    if (value == nullptr) {
        return {};
    }
    const string path(value);
    return Glib::file_test(path, Glib::FileTest::IS_DIR) ? path : string{};
}
