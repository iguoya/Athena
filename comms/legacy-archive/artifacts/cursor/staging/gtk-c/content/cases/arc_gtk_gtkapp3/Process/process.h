/*
 * process.h
 *
 *  Created on: 2022年10月15日
 *      Author: tiger
 */

#ifndef PROCESS_PROCESS_H_
#define PROCESS_PROCESS_H_
#include <gtk/gtk.h>
#include <unistd.h>

void return_window(GtkWidget *button, gpointer window);

void create_task(GtkButton *button, gpointer text_view);

#endif /* PROCESS_PROCESS_H_ */
