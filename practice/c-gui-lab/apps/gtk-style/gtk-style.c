/* GTK4 + libadwaita + CSS 样式橱窗。
 *
 * 展示 C 阵营里唯一「声明式美化」路线的三层能力：
 *   1. libadwaita 的设计语言（默认观感即成品）；
 *   2. CSS 子集做圆角/渐变/过渡（style.css 与 exe 同目录，运行时加载）；
 *   3. 运行时换肤：深色模式与 accent 色由 AdwStyleManager 即时切换。
 */

#include <adwaita.h>
#include <windows.h> /* GetModuleFileNameA：定位 exe 同目录的 style.css */

/* 三套 hero 渐变主题：运行时替换 CSS provider，验证声明式换肤的即时性 */
static const char *HERO_THEMES[] = {
    /* 海洋 */
    ".hero { background: linear-gradient(135deg, #1c71d8 0%, #3584e4 45%, #62a0ea 100%); }",
    /* 落日 */
    ".hero { background: linear-gradient(135deg, #e66100 0%, #ed333b 55%, #f66151 100%); }",
    /* 极光 */
    ".hero { background: linear-gradient(135deg, #241f31 0%, #26a269 60%, #33d17a 100%); }",
};

static GtkCssProvider *hero_provider = NULL;
static int hero_index = 0;
static int accent_index = 0;

/* 六组自定义强调色：libadwaita 没有运行时 set accent 的 API（只跟随系统），
 * 覆盖它的 @define-color 三件套就是官方换肤通道 */
static const char *ACCENTS[][3] = {
    { "#3584e4", "#3584e4", "#ffffff" }, /* 蓝 */
    { "#2190a4", "#2190a4", "#ffffff" }, /* 青 */
    { "#3a944a", "#3a944a", "#ffffff" }, /* 绿 */
    { "#c88800", "#c88800", "#ffffff" }, /* 黄 */
    { "#9141ac", "#9141ac", "#ffffff" }, /* 紫 */
    { "#e62d42", "#e62d42", "#ffffff" }, /* 红 */
};

static void
apply_dynamic_theme(void)
{
  GString *css = g_string_sized_new(512);
  g_string_append_printf(css,
                         "@define-color accent_bg_color %s;\n"
                         "@define-color accent_color %s;\n"
                         "@define-color accent_fg_color %s;\n",
                         ACCENTS[accent_index][0], ACCENTS[accent_index][1],
                         ACCENTS[accent_index][2]);
  g_string_append(css, HERO_THEMES[hero_index]);
  gtk_css_provider_load_from_string(hero_provider, css->str);
  g_string_free(css, TRUE);
}

static void
on_hero_cycle(GtkButton *button, gpointer user_data)
{
  (void)button;
  (void)user_data;
  hero_index = (hero_index + 1) % 3;
  apply_dynamic_theme();

  /* 让按钮上的标签跟着换，页面有回应感 */
  static const char *names[] = { "换一套：海洋", "换一套：落日", "换一套：极光" };
  gtk_button_set_label(button, names[hero_index]);
}

static gboolean
on_dark_toggle(GtkSwitch *sw, gboolean state, gpointer user_data)
{
  (void)user_data;
  AdwStyleManager *mgr = adw_style_manager_get_default();
  adw_style_manager_set_color_scheme(
      mgr, state ? ADW_COLOR_SCHEME_FORCE_DARK : ADW_COLOR_SCHEME_PREFER_LIGHT);
  return FALSE; /* 让开关走默认状态切换 */
}

static void
on_accent_changed(GtkCheckButton *btn, gpointer user_data)
{
  if (!gtk_check_button_get_active(btn))
    return;
  accent_index = GPOINTER_TO_INT(user_data);
  apply_dynamic_theme();
}

static gboolean
pulse_progress(gpointer data)
{
  gtk_progress_bar_pulse(GTK_PROGRESS_BAR(data));
  return G_SOURCE_CONTINUE;
}

static GtkWidget *
card(const char *title, GtkWidget *content)
{
  GtkWidget *box = gtk_box_new(GTK_ORIENTATION_VERTICAL, 12);
  gtk_widget_add_css_class(box, "card");
  gtk_widget_add_css_class(box, "card-pad");

  GtkWidget *label = gtk_label_new(title);
  gtk_widget_set_halign(label, GTK_ALIGN_START);
  gtk_widget_add_css_class(label, "title-3");
  gtk_box_append(GTK_BOX(box), label);

  gtk_box_append(GTK_BOX(box), content);
  return box;
}

static GtkWidget *
make_control_grid(void)
{
  GtkWidget *grid = gtk_grid_new();
  gtk_grid_set_row_spacing(GTK_GRID(grid), 18);
  gtk_grid_set_column_spacing(GTK_GRID(grid), 18);

  /* 按钮 */
  GtkWidget *btns = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 8);
  GtkWidget *b1 = gtk_button_new_with_label("Suggested");
  gtk_widget_add_css_class(b1, "suggested-action");
  GtkWidget *b2 = gtk_button_new_with_label("Destructive");
  gtk_widget_add_css_class(b2, "destructive-action");
  GtkWidget *b3 = gtk_button_new_with_label("Pill");
  gtk_widget_add_css_class(b3, "pill");
  GtkWidget *b4 = gtk_button_new_from_icon_name("edit-copy-symbolic");
  gtk_widget_add_css_class(b4, "flat");
  gtk_box_append(GTK_BOX(btns), b1);
  gtk_box_append(GTK_BOX(btns), b2);
  gtk_box_append(GTK_BOX(btns), b3);
  gtk_box_append(GTK_BOX(btns), b4);
  gtk_grid_attach(GTK_GRID(grid), card("按钮：语义色与形状类", btns), 0, 0, 1, 1);

  /* 开关 + 滑块 */
  GtkWidget *box2 = gtk_box_new(GTK_ORIENTATION_VERTICAL, 12);
  gtk_box_append(GTK_BOX(box2), gtk_switch_new());
  GtkWidget *scale = gtk_scale_new_with_range(GTK_ORIENTATION_HORIZONTAL, 0, 100, 1);
  gtk_range_set_value(GTK_RANGE(scale), 64);
  gtk_box_append(GTK_BOX(box2), scale);
  gtk_grid_attach(GTK_GRID(grid), card("开关与滑块", box2), 1, 0, 1, 1);

  /* 进度三兄弟 */
  GtkWidget *box3 = gtk_box_new(GTK_ORIENTATION_VERTICAL, 12);
  GtkWidget *pb = gtk_progress_bar_new();
  gtk_progress_bar_set_fraction(GTK_PROGRESS_BAR(pb), 0.72);
  gtk_box_append(GTK_BOX(box3), pb);
  GtkWidget *pulse = gtk_progress_bar_new();
  gtk_box_append(GTK_BOX(box3), pulse);
  g_timeout_add(320, pulse_progress, pulse);
  GtkWidget *level = gtk_level_bar_new_for_interval(0, 100);
  gtk_level_bar_set_value(GTK_LEVEL_BAR(level), 58);
  gtk_box_append(GTK_BOX(box3), level);
  gtk_grid_attach(GTK_GRID(grid), card("进度：进度条与级别条", box3), 0, 1, 1, 1);

  /* 行组件：AdwActionRow + 内嵌开关 */
  GtkWidget *rows = adw_preferences_group_new();
  GtkWidget *row1 = adw_action_row_new();
  adw_preferences_row_set_title(ADW_PREFERENCES_ROW(row1), "自动保存");
  adw_action_row_set_subtitle(ADW_ACTION_ROW(row1), "改动实时写入，无需手动确认");
  GtkWidget *sw1 = gtk_switch_new();
  gtk_switch_set_active(GTK_SWITCH(sw1), TRUE);
  adw_action_row_add_suffix(ADW_ACTION_ROW(row1), sw1);
  adw_preferences_group_add(ADW_PREFERENCES_GROUP(rows), row1);
  GtkWidget *row2 = adw_action_row_new();
  adw_preferences_row_set_title(ADW_PREFERENCES_ROW(row2), "检查更新");
  adw_action_row_set_subtitle(ADW_ACTION_ROW(row2), "每周启动时静默检查一次");
  GtkWidget *btn = gtk_button_new_with_label("立即检查");
  gtk_widget_add_css_class(btn, "suggested-action");
  gtk_widget_add_css_class(btn, "pill");
  adw_action_row_add_suffix(ADW_ACTION_ROW(row2), btn);
  adw_preferences_group_add(ADW_PREFERENCES_GROUP(rows), row2);
  gtk_grid_attach(GTK_GRID(grid), card("行组件：AdwActionRow", rows), 1, 1, 1, 1);

  /* 过渡动画：Revealer */
  GtkWidget *box5 = gtk_box_new(GTK_ORIENTATION_VERTICAL, 10);
  GtkWidget *reveal_btn = gtk_button_new_with_label("展开详情");
  GtkWidget *revealer = gtk_revealer_new();
  gtk_revealer_set_transition_type(GTK_REVEALER(revealer),
                                   GTK_REVEALER_TRANSITION_TYPE_SLIDE_DOWN);
  gtk_revealer_set_transition_duration(GTK_REVEALER(revealer), 450);
  GtkWidget *secret = gtk_label_new("这是被 CSS 过渡动画带出来的内容。");
  gtk_widget_add_css_class(secret, "dimmed");
  gtk_revealer_set_child(GTK_REVEALER(revealer), secret);
  g_signal_connect_swapped(reveal_btn, "clicked",
                           G_CALLBACK(gtk_revealer_set_reveal_child), revealer);
  g_object_set_data(G_OBJECT(reveal_btn), "revealer", revealer);
  gtk_box_append(GTK_BOX(box5), reveal_btn);
  gtk_box_append(GTK_BOX(box5), revealer);
  gtk_grid_attach(GTK_GRID(grid), card("过渡：GtkRevealer", box5), 0, 2, 2, 1);

  return grid;
}

static void
build_ui(AdwApplicationWindow *win)
{
  GtkWidget *root = gtk_box_new(GTK_ORIENTATION_VERTICAL, 0);
  GtkWidget *header = adw_header_bar_new();
  adw_header_bar_set_title_widget(ADW_HEADER_BAR(header),
                                  adw_window_title_new("GTK4 + Adwaita + CSS", NULL));
  gtk_box_append(GTK_BOX(root), header);

  GtkWidget *scroll = gtk_scrolled_window_new();
  gtk_scrolled_window_set_policy(GTK_SCROLLED_WINDOW(scroll), GTK_POLICY_NEVER,
                                 GTK_POLICY_AUTOMATIC);
  gtk_widget_set_vexpand(scroll, TRUE);
  gtk_box_append(GTK_BOX(root), scroll);

  GtkWidget *page = gtk_box_new(GTK_ORIENTATION_VERTICAL, 18);
  gtk_widget_set_margin_top(page, 24);
  gtk_widget_set_margin_bottom(page, 24);
  gtk_widget_set_margin_start(page, 28);
  gtk_widget_set_margin_end(page, 28);
  gtk_scrolled_window_set_child(GTK_SCROLLED_WINDOW(scroll), page);

  /* Hero：全部观感由 style.css 的 .hero 类决定 */
  GtkWidget *hero = gtk_box_new(GTK_ORIENTATION_VERTICAL, 8);
  gtk_widget_add_css_class(hero, "hero");
  GtkWidget *hero_title = gtk_label_new("声明式美化");
  gtk_widget_set_halign(hero_title, GTK_ALIGN_START);
  gtk_widget_add_css_class(hero_title, "hero-title");
  GtkWidget *hero_sub = gtk_label_new(
      "同一个控件树：libadwaita 出设计语言，CSS 出渐变与圆角，"
      "切换主题只改样式表、不改代码。");
  gtk_widget_set_halign(hero_sub, GTK_ALIGN_START);
  gtk_widget_set_halign(hero_sub, GTK_ALIGN_FILL);
  gtk_label_set_wrap(GTK_LABEL(hero_sub), TRUE);
  gtk_widget_add_css_class(hero_sub, "hero-sub");
  gtk_box_append(GTK_BOX(hero), hero_title);
  gtk_box_append(GTK_BOX(hero), hero_sub);
  gtk_box_append(GTK_BOX(page), hero);

  /* 主题控制行：深色开关 + accent 色 + hero 换肤 */
  GtkWidget *theme_row = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 14);
  GtkWidget *dark_row = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 8);
  GtkWidget *dark_label = gtk_label_new("深色模式");
  GtkWidget *dark_sw = gtk_switch_new();
  gtk_switch_set_active(GTK_SWITCH(dark_sw), TRUE);
  g_signal_connect(dark_sw, "state-set", G_CALLBACK(on_dark_toggle), NULL);
  gtk_box_append(GTK_BOX(dark_row), dark_label);
  gtk_box_append(GTK_BOX(dark_row), dark_sw);
  gtk_box_append(GTK_BOX(theme_row), dark_row);

  struct
  {
    const char *name;
    int index;
  } accents[] = {
    { "蓝", 0 }, { "青", 1 }, { "绿", 2 }, { "黄", 3 }, { "紫", 4 }, { "红", 5 },
  };
  GtkWidget *first_accent = NULL;
  for (guint i = 0; i < G_N_ELEMENTS(accents); i++)
    {
      GtkWidget *cb = gtk_check_button_new_with_label(accents[i].name);
      if (first_accent)
        gtk_check_button_set_group(GTK_CHECK_BUTTON(cb), GTK_CHECK_BUTTON(first_accent));
      else
        first_accent = cb; /* 第一个只当组锚点，不能把自己设进自己 */
      if (i == 0)
        gtk_check_button_set_active(GTK_CHECK_BUTTON(cb), TRUE);
      g_signal_connect(cb, "toggled", G_CALLBACK(on_accent_changed),
                       GINT_TO_POINTER(accents[i].index));
      gtk_box_append(GTK_BOX(theme_row), cb);
    }

  GtkWidget *spacer = gtk_label_new("");
  gtk_widget_set_hexpand(spacer, TRUE);
  gtk_box_append(GTK_BOX(theme_row), spacer);

  GtkWidget *hero_btn = gtk_button_new_with_label("换一套：海洋");
  gtk_widget_add_css_class(hero_btn, "pill");
  g_signal_connect(hero_btn, "clicked", G_CALLBACK(on_hero_cycle), NULL);
  gtk_box_append(GTK_BOX(theme_row), hero_btn);
  gtk_box_append(GTK_BOX(page), theme_row);

  gtk_box_append(GTK_BOX(page), make_control_grid());

  GtkWidget *foot = gtk_label_new(
      "官方合集是独立程序：gtk4-demo（控件画廊）与 adwaita-1-demo（设计语言橱窗），"
      "由 Electron 母体启动。");
  gtk_widget_set_halign(foot, GTK_ALIGN_START);
  gtk_widget_add_css_class(foot, "dimmed");
  gtk_label_set_wrap(GTK_LABEL(foot), TRUE);
  gtk_box_append(GTK_BOX(page), foot);

  adw_application_window_set_content(ADW_APPLICATION_WINDOW(win), root);
}

static void
on_activate(GtkApplication *app, gpointer user_data)
{
  (void)user_data;
  GtkWidget *win = adw_application_window_new(app);
  gtk_window_set_title(GTK_WINDOW(win), "GTK4 Style Gallery");
  gtk_window_set_default_size(GTK_WINDOW(win), 1080, 800);
  build_ui(ADW_APPLICATION_WINDOW(win));

  /* exe 同目录的 style.css 覆盖/补充 libadwaita 的默认样式 */
  char exe_path[MAX_PATH];
  GetModuleFileNameA(NULL, exe_path, MAX_PATH);
  char *dir = g_path_get_dirname(exe_path);
  char *css_path = g_build_filename(dir, "style.css", NULL);
  GFile *css_file = g_file_new_for_path(css_path);
  GtkCssProvider *provider = gtk_css_provider_new();
  gtk_css_provider_load_from_file(provider, css_file);
  gtk_style_context_add_provider_for_display(
      gdk_display_get_default(), GTK_STYLE_PROVIDER(provider),
      GTK_STYLE_PROVIDER_PRIORITY_APPLICATION);
  g_object_unref(css_file);
  g_free(css_path);
  g_free(dir);

  /* 动态主题（accent 三件套 + hero 渐变）走独立 provider，运行时整体替换 */
  hero_provider = gtk_css_provider_new();
  gtk_style_context_add_provider_for_display(
      gdk_display_get_default(), GTK_STYLE_PROVIDER(hero_provider),
      GTK_STYLE_PROVIDER_PRIORITY_APPLICATION + 1);
  apply_dynamic_theme();

  gtk_window_present(GTK_WINDOW(win));
}

int
main(int argc, char **argv)
{
  AdwApplication *app = adw_application_new("athena.c-gui-lab.gtk-style",
                                            G_APPLICATION_NON_UNIQUE);
  g_signal_connect(app, "activate", G_CALLBACK(on_activate), NULL);
  int status = g_application_run(G_APPLICATION(app), argc, argv);
  g_object_unref(app);
  return status;
}
