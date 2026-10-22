#include <gtk/gtk.h>

GtkWidget *label;
int main(int argc, char *argv[])
{
	GtkWidget *window;

	gtk_init (&argc, &argv);


	GtkBuilder *builder = gtk_builder_new();
	gtk_builder_add_from_file (builder, "ui.glade", NULL);

	window = GTK_WIDGET(gtk_builder_get_object(builder, "window_main"));
	gtk_builder_connect_signals(builder, NULL);

	label = GTK_WIDGET(gtk_builder_get_object(builder, "label"));
//	g_lbl_count = GTK_WIDGET(gtk_builder_get_object(builder, "label_name"));



	gtk_widget_show (window);

	gtk_main ();

	return 0;
}

void welcome()
{
//    static unsigned int count = 0;
//    char str_count[30] = {0};

	gtk_label_set_text(GTK_LABEL(label), "Hello, world!");
//    count++;
//    sprintf(str_count, "%d", count);
//    gtk_label_set_text(GTK_LABEL(g_lbl_count), str_count);
}
