#include <gtk/gtk.h>
void print_hello() {
	g_print("china");
}
int main(int argc, char *argv[])
{
	GtkWidget *window;
	GtkBuilder *builder;
	builder = gtk_builder_new ();
	gtk_init (&argc, &argv);

//	window = gtk_window_new (GTK_WINDOW_TOPLEVEL);
//
//	g_signal_connect (window, "destroy", G_CALLBACK (gtk_main_quit), NULL);
//
//	gtk_widget_show (window);

	gtk_builder_add_from_file (builder, "../layout.ui", NULL);
	window = gtk_builder_get_object (builder, "window");
	
	GtkButton *button = gtk_builder_get_object (builder, "button1");
	g_signal_connect (button, "clicked", G_CALLBACK (print_hello), NULL);
	gtk_widget_show_all(window);


	gtk_main ();

	return 0;
}
