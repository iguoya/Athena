/* -*- Mode: C; indent-tabs-mode: t; c-basic-offset: 4; tab-width: 4 -*-  */
/*
 * g28-pack.c
 * Copyright (C) 2022 tiger <tiger@loongnix>
 * 
 * g28-pack is free software: you can redistribute it and/or modify it
 * under the terms of the GNU General Public License as published by the
 * Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * 
 * g28-pack is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License along
 * with this program.  If not, see <http://www.gnu.org/licenses/>.
 */
#include "g28-pack.h"

#include <glib/gi18n.h>




G_DEFINE_TYPE (G28pack, g28_pack, GTK_TYPE_APPLICATION);

/* ANJUTA: Macro G28_PACK_APPLICATION gets G28pack - DO NOT REMOVE */

/* Create a new window loading a file */
static void
g28_pack_new_window (GApplication *app,
                           GFile        *file)
{
	GtkWidget *window;

	window = gtk_window_new (GTK_WINDOW_TOPLEVEL);
	gtk_window_set_title (GTK_WINDOW (window), "g28-pack");
	
	
	gtk_window_set_application (GTK_WINDOW (window), GTK_APPLICATION (app));
	if (file != NULL)
	{
		/* TODO: Add code here to open the file in the new window */
	}

	gtk_widget_show_all (GTK_WIDGET (window));
}


/* GApplication implementation */
static void
g28_pack_activate (GApplication *application)
{
	g28_pack_new_window (application, NULL);
}

static void
g28_pack_open (GApplication  *application,
                     GFile        **files,
                     gint           n_files,
                     const gchar   *hint)
{
	gint i;

	for (i = 0; i < n_files; i++)
		g28_pack_new_window (application, files[i]);
}

static void
g28_pack_init (G28pack *object)
{
}

static void
g28_pack_finalize (GObject *object)
{
	G_OBJECT_CLASS (g28_pack_parent_class)->finalize (object);
}

static void
g28_pack_class_init (G28packClass *klass)
{
	G_APPLICATION_CLASS (klass)->activate = g28_pack_activate;
	G_APPLICATION_CLASS (klass)->open = g28_pack_open;

	G_OBJECT_CLASS (klass)->finalize = g28_pack_finalize;
}

G28pack *
g28_pack_new (void)
{
	return g_object_new (g28_pack_get_type (),
	                     "application-id", "org.gnome.g28_pack",
	                     "flags", G_APPLICATION_HANDLES_OPEN,
	                     NULL);
}

