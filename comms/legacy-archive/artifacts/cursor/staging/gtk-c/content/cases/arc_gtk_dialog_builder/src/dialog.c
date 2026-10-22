/***************************************************************************
 *            dialog.c
 *
 *  二 五月 17 22:52:21 2022
 *  Copyright  2022  tiger
 *  <user@host>
 ****************************************************************************/
#include "gtk/gtk.h"

static void
print_hello (GtkWidget *widget,
             gpointer   data)
{
	g_print ("Hello World\n");
}
// Function to open a dialog box with a message
void
quick_message (GtkWindow *parent, gchar *message)
{
	GtkBuilder *builder;
	GObject *window;

	builder = gtk_builder_new ();
	gtk_builder_add_from_file (builder, "src/dialog.ui", NULL);
	/* Connect signal handlers to the constructed widgets. */
	window = gtk_builder_get_object (builder, "window");
/*	g_signal_connect (window, "destroy", G_CALLBACK (gtk_main_quit), NULL);
	button = gtk_builder_get_object (builder, "button1");
	g_signal_connect (button, "clicked", G_CALLBACK (print_hello), NULL);
	button = gtk_builder_get_object (builder, "button2");
	g_signal_connect (button, "clicked", G_CALLBACK (print_hello), NULL);
	button = gtk_builder_get_object (builder, "quit");
	g_signal_connect (button, "clicked", G_CALLBACK (gtk_main_quit), NULL);*/
	gtk_widget_show_all(window);
}