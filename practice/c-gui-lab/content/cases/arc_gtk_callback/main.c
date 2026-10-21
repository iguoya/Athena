#include <gtk/gtk.h>



void hello(GtkButton *button, gpointer user_data)
{
        const char *text = gtk_button_get_label(button);
 
        printf("%s----%s\n",(char *)user_data,  text );
 
        return;
}

void guoya(GtkButton *button, gpointer user_data)
{
        const char *text = gtk_button_get_label(button);
 
        printf("%s----%s\n",(char *)user_data,  text );
 
        return;
}




int main(int argc, char *argv[])
{
	GtkWidget *window;

	gtk_init (&argc, &argv);

	window = gtk_window_new (GTK_WINDOW_TOPLEVEL);

	g_signal_connect (window, "destroy", G_CALLBACK (gtk_main_quit), NULL);


        //3.1创建一个水平容器
        GtkWidget *hbox = gtk_box_new(GTK_ORIENTATION_VERTICAL,  50);
        //3.2将水平容器加入到窗口中
        gtk_container_add(GTK_CONTAINER(window), hbox);
 
	GtkWidget *button = gtk_button_new_with_label("你好");
	GtkWidget *button2 = gtk_button_new_with_label("郭雅");
	GtkWidget *button3 = gtk_button_new_with_label("旅行");
	GtkWidget *button4 = gtk_button_new_with_label("开心");
	
	
	gtk_container_add(GTK_CONTAINER(hbox), button);
	gtk_container_add(GTK_CONTAINER(hbox), button2);
	gtk_container_add(GTK_CONTAINER(hbox), button3);
	gtk_container_add(GTK_CONTAINER(hbox), button4);
	
	     g_signal_connect(button, "pressed", G_CALLBACK( hello ),  "World");
	  g_signal_connect(button2, "pressed", G_CALLBACK( guoya ),  "喜欢你");
//	  g_signal_connect(button2, "pressed", G_CALLBACK( travel ),  "喜欢你");

        gtk_widget_show_all(window);
//	gtk_widget_show (win {dow);

	gtk_main ();

	return 0;
}