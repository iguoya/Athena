#include "article_view.h"

#include <gdk/macos/gdkmacos.h>

#import <AppKit/AppKit.h>
#import <WebKit/WebKit.h>

using namespace std;

@interface AthenaArticleNavigationDelegate : NSObject <WKNavigationDelegate>
@end

@implementation AthenaArticleNavigationDelegate

- (void)webView:(WKWebView*)webView
    decidePolicyForNavigationAction:(WKNavigationAction*)navigationAction
                    decisionHandler:(void (^)(WKNavigationActionPolicy))decisionHandler {
    NSURL* url = navigationAction.request.URL;
    NSString* fragment = url.fragment;
    if (navigationAction.navigationType == WKNavigationTypeLinkActivated &&
        [fragment hasPrefix:@"athena-heading-"]) {
        NSString* script = [NSString stringWithFormat:
            @"document.getElementById('%@')?.scrollIntoView({behavior:'smooth',block:'start'});",
            fragment];
        [webView evaluateJavaScript:script completionHandler:nil];
        decisionHandler(WKNavigationActionPolicyCancel);
        return;
    }

    if (navigationAction.navigationType == WKNavigationTypeLinkActivated &&
        ([url.scheme isEqualToString:@"http"] ||
         [url.scheme isEqualToString:@"https"])) {
        [[NSWorkspace sharedWorkspace] openURL:url];
        decisionHandler(WKNavigationActionPolicyCancel);
        return;
    }

    decisionHandler(WKNavigationActionPolicyAllow);
}

@end

namespace {

class MacArticleView final : public ArticleView {
public:
    MacArticleView(Gtk::DrawingArea& host, Gtk::Window& window)
        : m_host(host),
          m_window(window),
          m_resize_connection(m_host.signal_resize().connect(
              sigc::mem_fun(*this, &MacArticleView::on_resize))),
          m_map_connection(m_host.signal_map().connect(
              sigc::mem_fun(*this, &MacArticleView::on_map))),
          m_unmap_connection(m_host.signal_unmap().connect(
              sigc::mem_fun(*this, &MacArticleView::on_unmap))) {}

    ~MacArticleView() override {
        m_resize_connection.disconnect();
        m_map_connection.disconnect();
        m_unmap_connection.disconnect();

        if (m_web_view) {
            [m_web_view stopLoading];
            m_web_view.navigationDelegate = nil;
            [m_web_view removeFromSuperview];
            m_web_view = nil;
        }
        m_navigation_delegate = nil;
    }

    void load_html(const string& html, const string& base_path) override {
        m_html = html;
        m_base_path = base_path;
        m_document_loaded = false;
        if (ensure_web_view()) {
            load_pending_document();
        }
    }

private:
    bool ensure_web_view() {
        if (m_web_view) {
            return true;
        }
        if (!m_host.get_mapped()) {
            return false;
        }

        GtkNative* native = gtk_widget_get_native(GTK_WIDGET(m_host.gobj()));
        if (!native) {
            return false;
        }

        GdkSurface* surface = gtk_native_get_surface(native);
        if (!surface || !GDK_IS_MACOS_SURFACE(surface)) {
            return false;
        }

        auto* native_window = (__bridge NSWindow*)
            gdk_macos_surface_get_native_window(GDK_MACOS_SURFACE(surface));
        if (!native_window || !native_window.contentView) {
            return false;
        }

        m_native_content_view = native_window.contentView;
        auto* configuration = [[WKWebViewConfiguration alloc] init];
        // Markdown 原始 HTML 已被解析器禁用；这里只运行应用生成的阅读设置脚本。
        configuration.defaultWebpagePreferences.allowsContentJavaScript = YES;

        m_web_view = [[WKWebView alloc] initWithFrame:NSZeroRect
                                       configuration:configuration];
        m_navigation_delegate = [[AthenaArticleNavigationDelegate alloc] init];
        m_web_view.navigationDelegate = m_navigation_delegate;
        m_web_view.autoresizingMask = NSViewNotSizable;
        [m_native_content_view addSubview:m_web_view];
        sync_frame();
        return true;
    }

    void load_pending_document() {
        if (!m_web_view || m_html.empty() || m_document_loaded) {
            return;
        }

        NSString* html = [NSString stringWithUTF8String:m_html.c_str()];
        NSURL* base_url = nil;
        if (!m_base_path.empty()) {
            NSString* path = [NSString stringWithUTF8String:m_base_path.c_str()];
            base_url = [NSURL fileURLWithPath:path isDirectory:YES];
        }
        [m_web_view loadHTMLString:html baseURL:base_url];
        m_document_loaded = true;
    }

    void on_map() {
        if (!ensure_web_view()) {
            return;
        }
        [m_web_view setHidden:NO];
        sync_frame();
        load_pending_document();
    }

    void on_unmap() {
        if (m_web_view) {
            [m_web_view setHidden:YES];
        }
    }

    void on_resize(int, int) {
        sync_frame();
    }

    void sync_frame() {
        if (!m_web_view || !m_native_content_view) {
            return;
        }

        graphene_rect_t bounds{};
        if (!gtk_widget_compute_bounds(
                GTK_WIDGET(m_host.gobj()),
                GTK_WIDGET(m_window.gobj()),
                &bounds)) {
            return;
        }

        CGFloat y = bounds.origin.y;
        if (![m_native_content_view isFlipped]) {
            y = NSHeight(m_native_content_view.bounds) - y - bounds.size.height;
        }

        m_web_view.frame = NSMakeRect(
            bounds.origin.x,
            y,
            bounds.size.width,
            bounds.size.height);
    }

    Gtk::DrawingArea& m_host;
    Gtk::Window& m_window;
    sigc::connection m_resize_connection;
    sigc::connection m_map_connection;
    sigc::connection m_unmap_connection;
    string m_html;
    string m_base_path;
    bool m_document_loaded = false;
    NSView* m_native_content_view = nil;
    WKWebView* m_web_view = nil;
    AthenaArticleNavigationDelegate* m_navigation_delegate = nil;
};

} // namespace

unique_ptr<ArticleView> create_platform_article_view(
    Gtk::DrawingArea& host,
    Gtk::Window& window) {
    return make_unique<MacArticleView>(host, window);
}
