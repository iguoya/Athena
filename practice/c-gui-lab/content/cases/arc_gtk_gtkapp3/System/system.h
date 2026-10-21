/*
 * system.h
 *
 *  Created on: 2022年10月15日
 *      Author: tiger
 */

#ifndef SYSTEM_SYSTEM_H_
#define SYSTEM_SYSTEM_H_

#include <gtk/gtk.h>

//enum {
//	column_id,
//	column_name,
////	column_input,
//	column_description,
//	n_columns
//};
//
//typedef struct
//{
//  const guint     number;
//  const gchar    *name;
//  const gchar    *description;
//} Bug;

GtkWidget *do_list_store (GtkWidget *button, gpointer do_widget);
//enum {col_name = 0, n_cols};

//void on_char_clicked(GtkWidget *button, gpointer tree_view);
//
//void set_list_store(GtkWidget *button, gpointer list_store);
//void set_tree_store_model(GtkWidget *button, gpointer tree_store);
////void on_list_store_row_changed(GtkWidget *list_store, gpointer tree_view);
//void on_string_clicked(GtkWidget *button, gpointer tree_view);

#endif /* SYSTEM_SYSTEM_H_ */
