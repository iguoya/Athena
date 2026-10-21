/*
 * share_memory.h
 *
 *  Created on: 2022年10月16日
 *      Author: tiger
 */

#ifndef IPC_IPC_H_
#define IPC_IPC_H_

#include <gtk/gtk.h>
#include <sys/mman.h>
#include <fcntl.h>
#include "public.h"

void create_ipc_dialog(GtkWidget *button, gpointer window);

void share_memory(GtkButton *button, gpointer text_view);

#endif /* IPC_IPC_H_ */
