/*
 * thread.c
 *
 *  Created on: 2022年10月15日
 *      Author: tiger
 */
#include "thread.h"



void *task(void *message) {
	TMessage *msg = (TMessage *)message;
	GString *content = g_string_new("");
	g_string_sprintf(content, "thread function is running : argument :%s\n", msg->content->str);
	text_view_append(msg->text_view, content);
	//	GString *content = g_string_new("thread function is running : argument :%s");
	//	g_string_append(content, msg->content);
	//	text_view_append(msg->text_view, content);
	sleep(2);
	//	g_string_free(msg->content);
	//	msg->content = g_string_new("bye");
	//	text_view_append(msg->text_view, g_string_append(content, "bye"));
	//	text_view_append(msg->text_view, g_string_new("guoya"));
	g_string_assign(msg->content, "guoya");

	pthread_exit("Thank you for the CPU time");
}


void create_thread(GtkButton *button,GtkTextView* text_view) {
	pthread_t thread[3] = {};
	TMessage *message = (TMessage *)malloc(sizeof(TMessage));
	message->text_view = text_view;
	message->content = g_string_new("hello world");

	//	char message[] = "hello world";
	int index = 0;
	for(; index < 3; ++index) {
		pthread_create(&thread[index], NULL, task, (void *)message);
	}
	GString *msg = g_string_new("create thread success \n waiting for thread to finish ...\n");
	text_view_append(text_view, msg);

	void *result;
	pthread_join(thread[0], &result);


	GString *content = g_string_new("");
	g_string_sprintf(content, "thread joined, return : %s\n", g_string_new((char *)result)->str);
	text_view_append(text_view, content);
//
	GString *now_message = g_string_new("");
	g_string_sprintf(now_message, "message is now : %s\n", message->content->str);
	text_view_append(text_view, now_message);

}

