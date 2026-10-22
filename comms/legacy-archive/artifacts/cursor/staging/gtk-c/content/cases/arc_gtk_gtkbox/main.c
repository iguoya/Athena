#include <gtk/gtk.h>

int main(int argc, char *argv[])
{
	GtkWidget *window;

	gtk_init (&argc, &argv);

	window = gtk_window_new (GTK_WINDOW_TOPLEVEL);

	g_signal_connect (window, "destroy", G_CALLBACK (gtk_main_quit), NULL);
    
    
    GtkBox *box = gtk_box_new(GTK_ORIENTATION_HORIZONTAL, 0);
    
    GtkButton *btn = gtk_button_new();
    gtk_button_set_label(btn, "唱歌");
    gtk_box_pack_start(box, btn, FALSE, FALSE, 0);
    gtk_widget_show(btn);
    
    GtkButton *btn2 = gtk_button_new();
    gtk_button_set_label(btn2, "跳舞");
    gtk_box_pack_start(box, btn2, FALSE, FALSE, 0);
    gtk_widget_show(btn2);
    
    GtkEntry *entry = gtk_entry_new();
    gtk_box_pack_start(box, entry, FALSE, FALSE, 0);  
    gtk_widget_show(entry);
    
    gtk_widget_show(box);
    gtk_container_add(window, box);

	gtk_widget_show (window);

	gtk_main ();

	return 0;
}