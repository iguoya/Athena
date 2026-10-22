#include <gtk/gtk.h>

void say(GtkButton *button, gpointer user_data)
{
	const char *text = gtk_button_get_label(button);

	printf("Hello, --->%s\n",(char *)user_data,  text );

	return;
}



int main(int argc, char *argv[])
{


	gtk_init (&argc, &argv);

//	window = gtk_window_new (GTK_WINDOW_TOPLEVEL);
//
//	g_signal_connect (window, "destroy", G_CALLBACK (gtk_main_quit), NULL);
//
//	gtk_widget_show (window);
	GtkBuilder *builder = gtk_builder_new();
	if ( !gtk_builder_add_from_file(builder,"../tiger.glade", NULL)) {
		printf("connot load file!");
	}

	GtkWidget *window  = GTK_WIDGET(gtk_builder_get_object(builder,"window"));
	GtkButton *buttonA = GTK_BUTTON(gtk_builder_get_object(builder, "me"));
	GtkButton *buttonB = GTK_BUTTON(gtk_builder_get_object(builder, "you"));
	GtkButton *buttonC = GTK_BUTTON(gtk_builder_get_object(builder, "love"));
	GtkButton *buttonD = GTK_BUTTON(gtk_builder_get_object(builder, "guoya"));



	const char *text = gtk_button_get_label(buttonD);

	printf("text=%s\n", text);


	g_signal_connect(buttonA, "pressed", G_CALLBACK( say ),   gtk_button_get_label(buttonA));
	g_signal_connect(buttonB, "pressed", G_CALLBACK( say ),   gtk_button_get_label(buttonB));
	g_signal_connect(buttonC, "pressed", G_CALLBACK( say ),   gtk_button_get_label(buttonC));
	g_signal_connect(buttonD, "pressed", G_CALLBACK( say ),   gtk_button_get_label(buttonD));


	gtk_widget_show_all(window);

	gtk_main ();

	return 0;
}
