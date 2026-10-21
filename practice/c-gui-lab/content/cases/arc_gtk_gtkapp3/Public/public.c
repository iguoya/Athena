/*
 * public.c
 *
 *  Created on: 2022年10月16日
 *      Author: tiger
 */
#include  "public.h"


void show_dialog(GtkButton *button, GtkWindow* parent) {
	//	g_print("hello\n");
	//	GError *error = NULL;
	GtkBuilder* builder = gtk_builder_new ();
	const gchar *name = gtk_button_get_label(button);

	GString *ui = g_string_new("ui/");
	if(strcmp(name, "多任务编程") == 0) {
		g_string_append(ui, "process.glade");
	} else if(strcmp(name, "系统函数") == 0){
		g_string_append(ui, "system.glade");
	} else if(strcmp(name, "进程间通信") == 0) {
		g_string_append(ui, "ipc.glade");
	} else if(strcmp(name, "多线程编程") == 0) {
		g_string_append(ui, "thread.glade");
	} else if(strcmp(name, "网络编程") == 0) {
		g_string_append(ui, "network.glade");
	} else if(strcmp(name, "设备驱动程序设计") == 0) {
		g_string_append(ui, "driver.glade");
	}

//	g_snprintf(ui_file, 30, "ui/%s.glade", data);

	//		g_print(ui_file);
	//	if (gtk_builder_add_from_file (builder, ui_file, &error) == 0)
	//	{
	//		g_printerr ("Error loading file: %s\n", error->message);
	//		g_clear_error (&error);
	//	}
	builder = gtk_builder_new_from_file(ui->str);

	GtkWidget *dialog = GTK_WIDGET(gtk_builder_get_object(builder, "dialog"));
	gtk_window_set_transient_for (GTK_WINDOW(dialog), parent);
	gtk_builder_connect_signals (builder, NULL);

	gtk_widget_hide(parent);
//	gtk_dialog_run();
//	gtk_widget_show_all(dialog);
	gtk_dialog_run(GTK_DIALOG(dialog));

//	gtk_widget_destroy(dialog);

	g_object_unref(G_OBJECT(builder));
//	GTK_RESPONSE_APPLY
//	  GTK_RESPONSE_YES          = -8,
//	  GTK_RESPONSE_NO           = -9,

//	g_print("response : %d", response);
//	if(response == GTK_RESPONSE_CLOSE) {
//		gtk_widget_hide(dialog);
//	}
}

void text_view_append(GtkTextView *text_view, GString *content) {

	GtkTextIter end;
	GtkTextBuffer *buffer = gtk_text_view_get_buffer (text_view);

	gtk_text_buffer_get_end_iter(buffer, &end);
	gtk_text_buffer_insert(buffer, &end, content->str, -1);
}
