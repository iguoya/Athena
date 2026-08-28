#pragma once

#include "registry/chapter_catalog.h"

#include <gtkmm.h>

void configure_icon_image(Gtk::Image& image, const IconSpec& icon, int pixel_size);
Gtk::Image* make_icon_image(const IconSpec& icon, int pixel_size);
