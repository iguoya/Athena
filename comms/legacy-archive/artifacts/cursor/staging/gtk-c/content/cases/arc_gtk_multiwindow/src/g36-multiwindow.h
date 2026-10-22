/* -*- Mode: C; indent-tabs-mode: t; c-basic-offset: 4; tab-width: 4 -*-  */
/*
 * g36-multiwindow.h
 * Copyright (C) 2022 tiger <tiger@loongnix>
 * 
 * g36-MultiWindow is free software: you can redistribute it and/or modify it
 * under the terms of the GNU General Public License as published by the
 * Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * 
 * g36-MultiWindow is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License along
 * with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

#ifndef _G36_MULTIWINDOW_
#define _G36_MULTIWINDOW_

#include <gtk/gtk.h>

G_BEGIN_DECLS

#define G36_MULTIWINDOW_TYPE_APPLICATION             (g36_multiwindow_get_type ())
#define G36_MULTIWINDOW_APPLICATION(obj)             (G_TYPE_CHECK_INSTANCE_CAST ((obj), G36_MULTIWINDOW_TYPE_APPLICATION, G36multiwindow))
#define G36_MULTIWINDOW_APPLICATION_CLASS(klass)     (G_TYPE_CHECK_CLASS_CAST ((klass), G36_MULTIWINDOW_TYPE_APPLICATION, G36multiwindowClass))
#define G36_MULTIWINDOW_IS_APPLICATION(obj)          (G_TYPE_CHECK_INSTANCE_TYPE ((obj), G36_MULTIWINDOW_TYPE_APPLICATION))
#define G36_MULTIWINDOW_IS_APPLICATION_CLASS(klass)  (G_TYPE_CHECK_CLASS_TYPE ((klass), G36_MULTIWINDOW_TYPE_APPLICATION))
#define G36_MULTIWINDOW_APPLICATION_GET_CLASS(obj)   (G_TYPE_INSTANCE_GET_CLASS ((obj), G36_MULTIWINDOW_TYPE_APPLICATION, G36multiwindowClass))

typedef struct _G36multiwindowClass G36multiwindowClass;
typedef struct _G36multiwindow G36multiwindow;
typedef struct _G36multiwindowPrivate G36multiwindowPrivate;

struct _G36multiwindowClass
{
	GtkApplicationClass parent_class;
};

struct _G36multiwindow
{
	GtkApplication parent_instance;

	G36multiwindowPrivate *priv;

};

GType g36_multiwindow_get_type (void) G_GNUC_CONST;
G36multiwindow *g36_multiwindow_new (void);

/* Callbacks */

G_END_DECLS

#endif /* _APPLICATION_H_ */

