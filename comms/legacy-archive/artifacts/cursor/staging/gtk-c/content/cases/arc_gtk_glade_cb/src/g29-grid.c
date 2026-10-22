/* -*- Mode: C; indent-tabs-mode: t; c-basic-offset: 4; tab-width: 4 -*-  */
/*
 * g29-grid.c
 * Copyright (C) 2022 tiger <tiger@loongnix>
 * 
 * g29-grid is free software: you can redistribute it and/or modify it
 * under the terms of the GNU General Public License as published by the
 * Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * 
 * g29-grid is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License along
 * with this program.  If not, see <http://www.gnu.org/licenses/>.
 */
#include "g29-grid.h"

#include <glib/gi18n.h>



/* For testing propose use the local (not installed) ui file */
/* #define UI_FILE PACKAGE_DATA_DIR"/ui/g29_grid.ui" */
#define UI_FILE "src/g29_grid.ui"
#define TOP_WINDOW "window"


G_DEFINE_TYPE (G29grid, g29_grid, GTK_TYPE_APPLICATION);

/* ANJUTA: Macro G29_GRID_APPLICATION gets G29grid - DO NOT REMOVE */
struct _G29gridPrivate
{
	/* ANJUTA: Widgets declaration for g29_grid.ui - DO NOT REMOVE */
};
void hello (GtkWidget *widget,
             gpointer   data)
{
  g_print ("Hello World\n");
}


void guoya (GtkWidget *widget,
             gpointer   data)
{
  g_print (" 郭雅 郭雅\n");
}


/* Create a new window loading a file */
static void
g29_grid_new_window (GApplication *app,
                           GFile        *file)
{
	GtkWidget *window;

	GtkBuilder *builder;
	GError* error = NULL;

	G29gridPrivate *priv = G29_GRID_APPLICATION(app)->priv;

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

/*		g_signal_connect (button, "clicked", G_CALLBACK (hello), NULL);*/


	
	/* ANJUTA: Widgets initialization for g29_grid.ui - DO NOT REMOVE */

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
g29_grid_activate (GApplication *application)
{
	g29_grid_new_window (application, NULL);
}

static void
g29_grid_open (GApplication  *application,
                     GFile        **files,
                     gint           n_files,
                     const gchar   *hint)
{
	gint i;

	for (i = 0; i < n_files; i++)
		g29_grid_new_window (application, files[i]);
}

static void
g29_grid_init (G29grid *object)
{
	object->priv = G_TYPE_INSTANCE_GET_PRIVATE (object, G29_GRID_TYPE_APPLICATION, G29gridPrivate);
}

static void
g29_grid_finalize (GObject *object)
{
	G_OBJECT_CLASS (g29_grid_parent_class)->finalize (object);
}

static void
g29_grid_class_init (G29gridClass *klass)
{
	G_APPLICATION_CLASS (klass)->activate = g29_grid_activate;
	G_APPLICATION_CLASS (klass)->open = g29_grid_open;

	g_type_class_add_private (klass, sizeof (G29gridPrivate));

	G_OBJECT_CLASS (klass)->finalize = g29_grid_finalize;
}

G29grid *
g29_grid_new (void)
{
	return g_object_new (g29_grid_get_type (),
	                     "application-id", "org.gnome.g29_grid",
	                     "flags", G_APPLICATION_HANDLES_OPEN,
	                     NULL);
}

