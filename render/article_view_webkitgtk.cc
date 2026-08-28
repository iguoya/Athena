#include "article_view.h"

#include <webkit/webkit.h>

#include <iostream>

using namespace std;

namespace {

class WebKitGtkArticleView final : public ArticleView {
public:
    WebKitGtkArticleView(Gtk::DrawingArea& host, Gtk::Window&) {
        m_web_view = WEBKIT_WEB_VIEW(webkit_web_view_new());
        g_signal_connect(
            m_web_view, "load-changed",
            G_CALLBACK(&WebKitGtkArticleView::on_load_changed), this);
        g_signal_connect(
            m_web_view, "load-failed",
            G_CALLBACK(&WebKitGtkArticleView::on_load_failed), this);
        g_signal_connect(
            m_web_view, "decide-policy",
            G_CALLBACK(&WebKitGtkArticleView::on_decide_policy), this);
        replace_host(host);
    }

    ~WebKitGtkArticleView() override {
        if (m_web_view) {
            webkit_web_view_stop_loading(m_web_view);
            gtk_widget_unparent(GTK_WIDGET(m_web_view));
        }
    }

    void load_html(const string& html, const string& base_path) override {
        m_navigation_finished = false;
        gchar* base_uri = base_path.empty()
            ? nullptr
            : g_filename_to_uri(base_path.c_str(), nullptr, nullptr);
        webkit_web_view_load_html(m_web_view, html.c_str(), base_uri);
        g_free(base_uri);
    }

    void scroll_to_anchor(const string& anchor) override {
        if (m_navigation_finished) {
            run_scroll_script(anchor);
        } else {
            m_pending_scroll_anchor = anchor;
        }
    }

private:
    static void on_load_changed(
        WebKitWebView*, WebKitLoadEvent event, gpointer user_data) {
        auto* self = static_cast<WebKitGtkArticleView*>(user_data);
        if (event != WEBKIT_LOAD_FINISHED) {
            return;
        }
        self->m_navigation_finished = true;
        if (!self->m_pending_scroll_anchor.empty()) {
            self->run_scroll_script(self->m_pending_scroll_anchor);
            self->m_pending_scroll_anchor.clear();
        }
    }

    static gboolean on_load_failed(
        WebKitWebView*, WebKitLoadEvent, const gchar*, GError* error, gpointer) {
        cerr << "ArticleView failed to load page: " << error->message << endl;
        return false;
    }

    static gboolean on_decide_policy(
        WebKitWebView*, WebKitPolicyDecision* decision,
        WebKitPolicyDecisionType type, gpointer user_data) {
        if (type != WEBKIT_POLICY_DECISION_TYPE_NAVIGATION_ACTION) {
            return false;
        }

        auto* navigation = WEBKIT_NAVIGATION_POLICY_DECISION(decision);
        auto* action = webkit_navigation_policy_decision_get_navigation_action(navigation);
        if (webkit_navigation_action_get_navigation_type(action) !=
            WEBKIT_NAVIGATION_TYPE_LINK_CLICKED) {
            return false;
        }

        auto* request = webkit_navigation_action_get_request(action);
        const gchar* uri = webkit_uri_request_get_uri(request);
        if (!uri) {
            return false;
        }

        GError* error = nullptr;
        GUri* parsed_uri = g_uri_parse(uri, G_URI_FLAGS_NONE, &error);
        if (parsed_uri && g_uri_get_fragment(parsed_uri)) {
            auto* self = static_cast<WebKitGtkArticleView*>(user_data);
            self->run_scroll_script(g_uri_get_fragment(parsed_uri));
            g_uri_unref(parsed_uri);
            webkit_policy_decision_ignore(decision);
            return true;
        }
        if (parsed_uri) {
            g_uri_unref(parsed_uri);
        }
        g_clear_error(&error);

        if (g_str_has_prefix(uri, "http://") || g_str_has_prefix(uri, "https://")) {
            GError* launch_error = nullptr;
            if (!g_app_info_launch_default_for_uri(uri, nullptr, &launch_error)) {
                cerr << "ArticleView failed to open external link: "
                     << launch_error->message << endl;
                g_clear_error(&launch_error);
            }
            webkit_policy_decision_ignore(decision);
            return true;
        }
        return false;
    }

    void replace_host(Gtk::DrawingArea& host) {
        auto* host_widget = GTK_WIDGET(host.gobj());
        auto* parent = gtk_widget_get_parent(host_widget);
        if (GTK_IS_FRAME(parent)) {
            gtk_frame_set_child(GTK_FRAME(parent), GTK_WIDGET(m_web_view));
            return;
        }
        if (GTK_IS_BOX(parent)) {
            gtk_box_remove(GTK_BOX(parent), host_widget);
            gtk_box_append(GTK_BOX(parent), GTK_WIDGET(m_web_view));
        }
    }

    void run_scroll_script(const string& anchor) {
        if (anchor.empty()) {
            return;
        }
        gchar* escaped = g_strescape(anchor.c_str(), nullptr);
        const string script =
            "document.getElementById('" + string(escaped) +
            "')?.scrollIntoView({behavior:'smooth',block:'start'});";
        g_free(escaped);
        webkit_web_view_evaluate_javascript(
            m_web_view, script.c_str(), -1, nullptr, nullptr, nullptr, nullptr, nullptr);
    }

    WebKitWebView* m_web_view = nullptr;
    bool m_navigation_finished = false;
    string m_pending_scroll_anchor;
};

} // namespace

unique_ptr<ArticleView> create_platform_article_view(
    Gtk::DrawingArea& host,
    Gtk::Window& window) {
    return make_unique<WebKitGtkArticleView>(host, window);
}
