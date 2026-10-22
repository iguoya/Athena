/*
 * share_memory.c
 *
 *  Created on: 2022年10月16日
 *      Author: tiger
 */
#include "ipc.h"




void share_memory(GtkButton *button, gpointer text_view) {

	GString *content =g_string_new("使用od 查看Tiger文件 ...");
	text_view_append(text_view, content);

	int fd = open("Guoya", O_RDWR);
	if(fd < 0) {
		perror("open error");
		return;
	}

	int *p = mmap(NULL, 12, PROT_WRITE, MAP_SHARED, fd, 0);
	close(fd);
	p[0] = 0x30313233;
	p[1] = 0x61626364;

	munmap(p, 12);


	//	GtkTextIter end;
	//	GtkTextBuffer *buffer = gtk_text_view_get_buffer (text_view));
	//
	////	const gchar *line = gtk_button_get_label (button);
	////	gtk_text_buffer_set_text (buffer, line, -1);
	//
	//	gtk_text_buffer_get_end_iter(buffer, &end);
	//	gtk_text_buffer_insert(buffer, &end, "共享内存ssss mmap :\n", -1);


}

