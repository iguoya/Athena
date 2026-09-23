#include "icon_utils.h"

#include <string>
#include <string_view>

using namespace std;

void configure_icon_image(
    Gtk::Image& image,
    const IconSpec& icon,
    int pixel_size) {
    if (icon.type == "resource" && !icon.path.empty()) {
        string resource_path = icon.path;
        constexpr string_view resources_prefix = "resources/";
        if (resource_path.rfind(resources_prefix, 0) == 0) {
            resource_path = "/app/" + resource_path.substr(resources_prefix.size());
        }
        image.set_from_resource(resource_path);
    } else if (!icon.name.empty()) {
        image.set_from_icon_name(icon.name);
    } else {
        image.set_visible(false);
        return;
    }
    image.set_pixel_size(pixel_size);
}

Gtk::Image* make_icon_image(const IconSpec& icon, int pixel_size) {
    auto image = Gtk::make_managed<Gtk::Image>();
    configure_icon_image(*image, icon, pixel_size);
    return image;
}
