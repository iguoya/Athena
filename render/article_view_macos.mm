#include "article_view.h"

#include <gdk/macos/gdkmacos.h>

#import <AppKit/AppKit.h>
#import <WebKit/WebKit.h>

#include <iostream>

using namespace std;

@interface AthenaArticleNavigationDelegate : NSObject <WKNavigationDelegate>
// 页面（含 baseURL 相关资源）加载完成时触发一次；MacArticleView 用它来
// 把"页面还没加载完就先请求跳锚点"的请求推迟到这个时机再执行。
@property (nonatomic, copy) void (^didFinishHandler)(void);
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

- (void)webView:(WKWebView*)webView didFinishNavigation:(WKNavigation*)navigation {
    if (self.didFinishHandler) {
        self.didFinishHandler();
    }
}

- (void)webView:(WKWebView*)webView
    didFailProvisionalNavigation:(WKNavigation*)navigation
                      withError:(NSError*)error {
    cerr << "ArticleView failed to load page: "
         << error.localizedDescription.UTF8String << endl;
}

- (void)webView:(WKWebView*)webView
    didFailNavigation:(WKNavigation*)navigation
             withError:(NSError*)error {
    cerr << "ArticleView navigation failed: "
         << error.localizedDescription.UTF8String << endl;
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
        m_pending_sync_connection.disconnect();

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

    void scroll_to_anchor(const string& anchor) override {
        if (m_navigation_finished) {
            run_scroll_script(anchor);
        } else {
            // 页面还在加载（或者压根还没开始加载），记下来，等
            // didFinishNavigation 触发时再执行，不丢失这次请求。
            m_pending_scroll_anchor = anchor;
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
        m_navigation_delegate.didFinishHandler = [this]() {
            on_navigation_finished();
        };
        [m_native_content_view addSubview:m_web_view];
        sync_frame();
        // 首次创建时 article_host 往往还没经过真正的布局分配，这里立即
        // 算出的 bounds 可能是 0 大小，WebView 因此不可见；额外排一次
        // idle 回调，等当前这轮布局跑完、真正的分配结果出来后再校正
        // 一次尺寸，兜底首帧时序问题。
        m_pending_sync_connection.disconnect();
        m_pending_sync_connection = Glib::signal_idle().connect([this]() {
            sync_frame();
            return false;
        });
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
        m_navigation_finished = false;
        [m_web_view loadHTMLString:html baseURL:base_url];
        m_document_loaded = true;
    }

    void on_navigation_finished() {
        m_navigation_finished = true;
        if (!m_pending_scroll_anchor.empty()) {
            run_scroll_script(m_pending_scroll_anchor);
            m_pending_scroll_anchor.clear();
        }
    }

    void run_scroll_script(const string& anchor) {
        if (!m_web_view || anchor.empty()) {
            return;
        }
        NSString* script = [NSString stringWithFormat:
            @"document.getElementById('%s')?.scrollIntoView({behavior:'smooth',block:'start'});",
            anchor.c_str()];
        [m_web_view evaluateJavaScript:script completionHandler:nil];
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
    sigc::connection m_pending_sync_connection;
    string m_html;
    string m_base_path;
    bool m_document_loaded = false;
    // WKWebView 是否已经把当前这份 HTML 加载完（didFinishNavigation 触发
    // 过）；scroll_to_anchor 在加载完成前调用时，先记到
    // m_pending_scroll_anchor，等 on_navigation_finished 里再补跑。
    bool m_navigation_finished = false;
    string m_pending_scroll_anchor;
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
