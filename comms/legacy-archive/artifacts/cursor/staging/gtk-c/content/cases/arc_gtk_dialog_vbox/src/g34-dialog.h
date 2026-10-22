/* -*- Mode: C; indent-tabs-mode: t; c-basic-offset: 4; tab-width: 4 -*-  */
/*
 * g34-dialog.h
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

#ifndef _G34_DIALOG_
#define _G34_DIALOG_

#include <gtk/gtk.h>

G_BEGIN_DECLS

#define G34_DIALOG_TYPE_APPLICATION             (g34_dialog_get_type ())
#define G34_DIALOG_APPLICATION(obj)             (G_TYPE_CHECK_INSTANCE_CAST ((obj), G34_DIALOG_TYPE_APPLICATION, G34dialog))
#define G34_DIALOG_APPLICATION_CLASS(klass)     (G_TYPE_CHECK_CLASS_CAST ((klass), G34_DIALOG_TYPE_APPLICATION, G34dialogClass))
#define G34_DIALOG_IS_APPLICATION(obj)          (G_TYPE_CHECK_INSTANCE_TYPE ((obj), G34_DIALOG_TYPE_APPLICATION))
#define G34_DIALOG_IS_APPLICATION_CLASS(klass)  (G_TYPE_CHECK_CLASS_TYPE ((klass), G34_DIALOG_TYPE_APPLICATION))
#define G34_DIALOG_APPLICATION_GET_CLASS(obj)   (G_TYPE_INSTANCE_GET_CLASS ((obj), G34_DIALOG_TYPE_APPLICATION, G34dialogClass))

typedef struct _G34dialogClass G34dialogClass;
typedef struct _G34dialog G34dialog;
typedef struct _G34dialogPrivate G34dialogPrivate;

struct _G34dialogClass
{
	GtkApplicationClass parent_class;
};

struct _G34dialog
{
	GtkApplication parent_instance;

	G34dialogPrivate *priv;

};

GType g34_dialog_get_type (void) G_GNUC_CONST;
G34dialog *g34_dialog_new (void);

/* Callbacks */

G_END_DECLS

#endif /* _APPLICATION_H_ */

