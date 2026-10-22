/*
 * thread.h
 *
 *  Created on: 2022年10月15日
 *      Author: tiger
 */

#ifndef THREAD_THREAD_H_
#define THREAD_THREAD_H_
#include <gtk/gtk.h>
#include <pthread.h>
#include "public.h"


typedef struct TMessage {
	GtkTextView* text_view;
	GString *content;
} TMessage;

void *task(void *message);
void create_thread(GtkButton *button,GtkTextView* text_view);

#endif /* THREAD_THREAD_H_ */
