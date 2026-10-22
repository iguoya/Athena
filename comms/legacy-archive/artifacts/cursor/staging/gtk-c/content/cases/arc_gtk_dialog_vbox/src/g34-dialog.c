/* -*- Mode: C; indent-tabs-mode: t; c-basic-offset: 4; tab-width: 4 -*-  */
/*
 * g34-dialog.c
 * Copyright (C) 2022 tiger <tiger@loongnix>
 * 
 * g34-dialog is free software: you can redistribute it and/or modify it
 * under the terms of the GNU General Public License as published by the
 * Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * 
 * g34-dialog is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License along
 * with this program.  If not, see <http://www.gnu.org/licenses/>.
 */
#include "g34-dialog.h"

#include <glib/gi18n.h>



/* For testing propose use the local (not installed) ui file */
/* #define UI_FILE PACKAGE_DATA_DIR"/ui/g34_dialog.ui" */
#define UI_FILE "src/g34_dialog.ui"
#define TOP_WINDOW "window"


G_DEFINE_TYPE (G34dialog, g34_dialog, GTK_TYPE_APPLICATION);

/* ANJUTA: Macro G34_DIALOG_APPLICATION gets G34dialog - DO NOT REMOVE */
struct _G34dialogPrivate
{
	/* ANJUTA: Widgets declaration for g34_dialog.ui - DO NOT REMOVE */
};
static int num = 0;
void hello() {
	g_print("郭雅 %d \n", num);
	++num;
}
void about_dialog_show() {
/*	gtk_button_released(p_widget);*/
    GtkWidget *p_window;
    GtkWidget *p_v_box;
    GtkWidget *p_entry;

    p_window = gtk_window_new(GTK_WINDOW_TOPLEVEL);
    gtk_window_set_title(GTK_WINDOW(p_window), "Create DB");
    gtk_window_set_default_size(GTK_WINDOW(p_window), 320, 200);

    p_v_box = gtk_vbox_new(TRUE, 0);
    gtk_container_add(GTK_CONTAINER(p_window), p_v_box);

    p_entry = gtk_entry_new();
    gtk_box_pack_start(GTK_BOX(p_v_box), p_entry, TRUE, FALSE, 0);
    gtk_widget_show_all(p_window);
}


/* Create a new window loading a file */
static void
g34_dialog_new_window (GApplication *app,
                           GFile        *file)
{
	GtkWidget *window;

	GtkBuilder *builder;
	GError* error = NULL;

	G34dialogPrivate *priv = G34_DIALOG_APPLICATION(app)->priv;

	/* Load UI from file */
	builder = gtk_builder_new ();
	if (!gtk_builder_add_from_file (builder, UI_FILE, &error))
	{
		g_critical ("Couldn't load builder file: %s", error->message);
		g_error_free (error);
	}

	/* Auto-connect signal handlers */
	gtk_builder_connect_signals (builder, app);

	/* Get the window object from the ui file */
	window = GTK_WIDGET (gtk_builder_get_object (builder, TOP_WINDOW));
        if (!window)
        {
		g_critical ("Widget \"%s\" is missing in file %s.",
				TOP_WINDOW,
				UI_FILE);
        }

	
	/* ANJUTA: Widgets initialization for g34_dialog.ui - DO NOT REMOVE */

	g_object_unref (builder);
	
	
	gtk_window_set_application (GTK_WINDOW (window), GTK_APPLICATION (app));
	if (file != NULL)
	{
		/* TODO: Add code here to open the file in the new window */
	}

	gtk_widget_show_all (GTK_WIDGET (window));
}


/* GApplication implementation */
static void
g34_dialog_activate (GApplication *application)
{
	g34_dialog_new_window (application, NULL);
}

static void
g34_dialog_open (GApplication  *application,
                     GFile        **files,
                     gint           n_files,
                     const gchar   *hint)
{
	gint i;

	for (i = 0; i < n_files; i++)
		g34_dialog_new_window (application, files[i]);
}

static void
g34_dialog_init (G34dialog *object)
{
	object->priv = G_TYPE_INSTANCE_GET_PRIVATE (object, G34_DIALOG_TYPE_APPLICATION, G34dialogPrivate);
}

static void
g34_dialog_finalize (GObject *object)
{
	G_OBJECT_CLASS (g34_dialog_parent_class)->finalize (object);
}

static void
g34_dialog_class_init (G34dialogClass *klass)
{
	G_APPLICATION_CLASS (klass)->activate = g34_dialog_activate;
	G_APPLICATION_CLASS (klass)->open = g34_dialog_open;

	g_type_class_add_private (klass, sizeof (G34dialogPrivate));

	G_OBJECT_CLASS (klass)->finalize = g34_dialog_finalize;
}

G34dialog *
g34_dialog_new (void)
{
	return g_object_new (g34_dialog_get_type (),
	                     "application-id", "org.gnome.g34_dialog",
	                     "flags", G_APPLICATION_HANDLES_OPEN,
	                     NULL);
}

