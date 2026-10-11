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

Gtk::Box* make_star_row(int filled, int pixel_size, int spacing) {
    auto row = Gtk::make_managed<Gtk::Box>(Gtk::Orientation::HORIZONTAL, spacing);
    for (int index = 0; index < kStarCount; ++index) {
        auto star = Gtk::make_managed<Gtk::Image>();
        star->set_pixel_size(pixel_size);
        row->append(*star);
    }
    set_star_row(*row, filled);
    return row;
}

void set_star_row(Gtk::Box& row, int filled) {
    int index = 0;
    for (auto child = row.get_first_child(); child; child = child->get_next_sibling()) {
        if (auto star = dynamic_cast<Gtk::Image*>(child)) {
            star->set_from_icon_name(
                index < filled ? "starred-symbolic" : "non-starred-symbolic");
            ++index;
        }
    }
}
