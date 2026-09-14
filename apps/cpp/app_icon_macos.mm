#include "app_icon.h"

#include <gdk-pixbuf/gdk-pixbuf.h>
#include <stdlib.h>
#include <unistd.h>

#import <AppKit/AppKit.h>

// macOS 裸可执行运行时，GTK 不会把窗口图标同步到 Dock；
// 需要显式设置 NSApplication 图标。NSImage 不解析 SVG，
// 先经 GdkPixbuf 解码为 PNG 临时文件再加载。
void apply_runtime_application_icon() {
    GdkPixbuf* pixbuf = gdk_pixbuf_new_from_resource_at_scale(
        "/app/icons/scalable/apps/cn.athena.icon.svg",
        128,
        128,
        TRUE,
        nullptr);
    if (!pixbuf) {
        return;
    }

    char path[] = "/tmp/athena-dock-icon-XXXXXX.png";
    const int descriptor = mkstemps(path, 4);
    if (descriptor < 0) {
        g_object_unref(pixbuf);
        return;
    }
    close(descriptor);

    if (gdk_pixbuf_save(pixbuf, path, "png", nullptr, nullptr)) {
        NSImage* image = [[NSImage alloc]
            initWithContentsOfFile:[NSString stringWithUTF8String:path]];
        if (image) {
            [NSApp setApplicationIconImage:image];
        }
    }
    unlink(path);
    g_object_unref(pixbuf);
}
