
#include <stdio.h>
#include <gtk/gtk.h>
#include <stdlib.h>
 
void setCss(GtkWidget *widget, const gchar *data)
{
    GtkCssProvider *provider = gtk_css_provider_new ();
    GtkStyleContext *context = gtk_widget_get_style_context(widget);
    gtk_css_provider_load_from_data(provider, data, -1, NULL);
    gtk_style_context_add_provider(context, GTK_STYLE_PROVIDER(provider), GTK_STYLE_PROVIDER_PRIORITY_USER);
    g_object_unref (provider);
}
 
int main(int  argc, char *argv[]) {
    GtkWidget *window;
    gtk_init(&argc, &argv);
    window = gtk_window_new(GTK_WINDOW_TOPLEVEL);
    gtk_window_set_title(GTK_WINDOW(window), "hello, ubuntu gtk");
    g_signal_connect(G_OBJECT(window), "destroy", G_CALLBACK(gtk_main_quit), NULL);
    gtk_widget_show(window);
    setCss (window, "window{border-radius:50px;background-color:green}");
    gtk_main();
    return 0;
}