/*
 * process.c
 *
 *  Created on: 2022年10月15日
 *      Author: tiger
 */
#include "process.h"

void return_window(GtkWidget *button, gpointer window) {
	//	gtk_widget_hide(window);
}

void create_task(GtkButton *button, gpointer text_view) {

    GString *content =g_string_new("创建进程.....");
    text_view_append(text_view, content);

//
//	GtkTextIter end;
//	GtkTextBuffer *buffer = gtk_text_view_get_buffer (GTK_TEXT_VIEW (textView));
//
//	const gchar *line = gtk_button_get_label (button);
//	gtk_text_buffer_set_text (buffer, line, -1);
//
//	gtk_text_buffer_get_end_iter(buffer, &end);
	//	 GtkTextIter iter;
	//	gtk_text_buffer_get_iter_at_offset(buffer, &iter, 0);

	//	gtk_text_buffer_insert(buffer, &end, "Plain text\n", -1);
	//    gtk_text_buffer_set_text (buffer, "Hello, this is some text", -1);
	//
	//	int children = fork();
	//	int status = 0;
	//	gchar *msg;
	//	if(children == 0) {
	////		msg = g_strdup();
	//		gtk_text_buffer_insert(buffer, &end, "I am son ", -1);
	////		gtk_text_buffer_get_end_iter(buffer, &end);
	////		gtk_text_buffer_insert(buffer, &end, msg, -1);
	//	} else {
	////		gchar *msg = "I am father ....";
	////		if(waitpid(children, &status, 0) == children) {
	////			gchar *
	////			msg = g_strjoin("\n", msg, "son finished , ready to start father ...", NULL);
	//////		}
	////
	////		gtk_text_buffer_get_end_iter(buffer, &end);
	////		gtk_text_buffer_insert(buffer, &end, msg, -1);
	////		gtk_text_buffer_insert(buffer, &end, "I am son ", -1);
	//	}
//	gtk_text_buffer_insert(buffer, &end, "\nI am son \n", -1);
	//
	//	gtk_text_buffer_get_end_iter(buffer, &end);
	//	gtk_text_buffer_insert(buffer, &end, msg, -1);

}

void create_process_dialog(GtkWidget *button, GtkWidget* parent) {
	//	g_print("hello\n");
//	GError *error = NULL;
//	GtkBuilder* builder = gtk_builder_new ();
//	//	    gtk_builder_add_from_file (builder, "tutorial.glade", NULL);
//	if (gtk_builder_add_from_file (builder, "ui/process_dialog.glade", &error) == 0)
//	{
//		g_printerr ("Error loading file: %s\n", error->message);
//		g_clear_error (&error);
//	}
//	GtkWidget *dialog = GTK_WIDGET(gtk_builder_get_object(builder,"dialog"));
	//	GtkWidget* window = GTK_WIDGET(gtk_builder_get_object (builder, "window"));
	//	GtkButton *return_button = GTK_BUTTON(gtk_builder_get_object(builder, "return"));
	//	g_signal_connect (return_button, "clicked", G_CALLBACK (return_window), parent);
	//			    GtkWidget *window = GTK_WIDGET (gtk_builder_get_object (builder, "../window"));
//	gtk_builder_connect_signals (builder, NULL);
//
//	g_object_unref (G_OBJECT (builder));
//	gtk_widget_show_all(dialog);
	//	gtk_widget_hide(parent);
	//	gtk_window_show();

	//	window = gtk_new_window();

	//	GtkWidget *window = gtk_window_new(GTK_WINDOW_TOPLEVEL);
	//
	//	gtk_window_set_title (GTK_WINDOW (window), "Window");
	//	gtk_window_set_default_size (GTK_WINDOW (window), 800, 600);
	//	gtk_widget_show_all (window);
	//	  GtkWidget *dialog;
	//	  dialog = gtk_message_dialog_new(GTK_WINDOW(window),
	//	            GTK_DIALOG_DESTROY_WITH_PARENT,
	//	            GTK_MESSAGE_INFO,
	//	            GTK_BUTTONS_OK,
	//	            "Download Completed");
	//	  gtk_window_set_title(GTK_WINDOW(dialog), "Information");
	//	  gtk_dialog_run(GTK_DIALOG(dialog));
	//	  gtk_widget_destroy(dialog);


	//
	//	GtkWidget *dialog;
	//	GtkWidget *label;
	//	GtkWidget *image;
	//	GtkWidget *hbox;
	//
	//	/*GtkWidget * gtk_dialog_new_with_buttons(
	//	 *           const gchar *title,对话框标题
	//	 *           GtkWindow *parent,对话框父窗口
	//	 *           GtkDialogFlags flags,
	//	 *           const gchar *first_button_text,动作区域按钮列表
	//	 *           ...);
	//	 *           falgs:GTK_DIALOG_MODAL:对话框始终保持在父窗口的上部，直到关闭，防止父窗口交互
	//	 *                 GTK_DIALOG_DESTROY_WITH_PARENT:父窗口销毁，对话框也销毁
	//	 *                 GTK_DIALOG_NO_SEPARATOR:不显示分割线
	//	 *
	//	 * */
	//
	//	dialog = gtk_dialog_new_with_buttons("我的第一个对话框",parent,GTK_DIALOG_MODAL,GTK_STOCK_OK,GTK_RESPONSE_OK,NULL);
	//
	//	/*设置分割线是否隐藏：FALSE：隐藏。*/
	//	//	    gtk_dialog_set_has_separator(GTK_DIALOG(dialog),FALSE);
	//	label = gtk_label_new("the button was clicked!");
	//	//
	//	//	    hbox = gtk_box_new(FALSE,5);
	//	//	    gtk_container_set_border_width(GTK_CONTAINER(hbox),10);
	//	//	    gtk_box_pack_start_defaults(GTK_BOX(hbox),image);
	//	//	    gtk_box_pack_start_defaults(GTK_BOX(hbox),label);
	//	//	    gtk_box_pack_start_defaults(GTK_BOX(GTK_DIALOG(dialog)->vbox),hbox);
	//	gtk_widget_show_all(dialog);

	//	#ifndef SCHEMALESS_WINDOW
	//	    /*显示对话框*/
	//	    gtk_dialog_run(GTK_DIALOG(dialog));
	//	    gtk_widget_destroy(dialog);
	//	#else
	//	    g_signal_connect(G_OBJECT(dialog),"response",G_CALLBACK(gtk_widget_destroy),NULL);
	//	#endif




	//	g_print("hello\n");
	//	GtkWidget *dialog, *label, *content_area;
	//	GtkDialogFlags flags;
	//
	//	// Create the widgets
	//	flags = GTK_DIALOG_DESTROY_WITH_PARENT;
	//	dialog = gtk_dialog_new_with_buttons ("Message",
	//			parent,
	//			flags,
	//			("_OK"),
	//			GTK_RESPONSE_NONE,
	//			NULL);
	//	content_area = gtk_dialog_get_content_area (GTK_DIALOG (dialog));
	//	label = gtk_label_new (message);
	//
	//	// Ensure that the dialog box is destroyed when the user responds
	//
	//	g_signal_connect_swapped (dialog,
	//			"response",
	//			G_CALLBACK (gtk_widget_destroy),
	//			dialog);
	//
	//	// Add the label, and show everything we’ve added
	//
	//	gtk_container_add (GTK_CONTAINER (content_area), label);
	//	gtk_widget_show_all (dialog);
	//	//1.gtk初始化
	//	gtk_init(&argc,&argv);
	//
	//	//2.创建GtkBuilder对象，GtkBuilder在<gtk/gtk.h>声明
	//	GtkBuilder *builder = gtk_builder_new();
	//
	//	//3.读取test.glade文件的信息，保存在builder中
	//	if ( !gtk_builder_add_from_file(builder,"test.glade", NULL)) {
	//		printf("connot load file!");
	//	}
	//
	//	//4.获取窗体指针，注意"window1"要和glade里面的标签名词匹配
	//	GtkWidget *window = GTK_WIDGET(gtk_builder_get_object(builder,"window1"));
	//
	//	GtkButton *button = GTK_BUTTON(gtk_builder_get_object(builder, "button1"));
	//
	//	const char *text = gtk_button_get_label(button);
	//	printf("text=%s\n", text);
	//	gtk_widget_show_all(window);
	//
	//	gtk_main();




	//	GtkWidget *window;
	////	window = gtk_new_window();
	//
	//    window = gtk_window_new(GTK_WINDOW_TOPLEVEL);
	//
	//	gtk_window_set_title (GTK_WINDOW (window), "Window");
	//	gtk_window_set_default_size (GTK_WINDOW (window), 800, 600);
	//	gtk_widget_show_all (window);

	//	GError *error = NULL;
	//	GtkBuilder* builder = gtk_builder_new ();
	//	if (gtk_builder_add_from_file (builder, "interface/process.glade", &error) == 0)
	//	{
	//		g_printerr ("Error loading file: %s\n", error->message);
	//		g_clear_error (&error);
	//	}
	//
	//	//		app = gtk_builder_get_application (builder);
	//	//		GtkWidget *window = gtk_application_window_new (app);
	//	GtkWidget *window = GTK_WIDGET (gtk_builder_get_object (builder, "interface/process.glade"));
	//	gtk_builder_connect_signals (builder, NULL);//连接响应事件
	//	g_object_unref(G_OBJECT(builder));
	//	gtk_widget_show_all (window);

}
