/* -*- Mode: C; indent-tabs-mode: t; c-basic-offset: 4; tab-width: 4 -*-  */
/*
 * g17-anjuta.h
 * Copyright (C) 2022 tiger <tiger@msi>
 * 
 * G17-Anjuta is free software: you can redistribute it and/or modify it
 * under the terms of the GNU General Public License as published by the
 * Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * 
 * G17-Anjuta is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License along
 * with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

#ifndef _G17_ANJUTA_
#define _G17_ANJUTA_

#include <gtk/gtk.h>

G_BEGIN_DECLS

#define G17_ANJUTA_TYPE_APPLICATION             (g17_anjuta_get_type ())
#define G17_ANJUTA_APPLICATION(obj)             (G_TYPE_CHECK_INSTANCE_CAST ((obj), G17_ANJUTA_TYPE_APPLICATION, G17anjuta))
#define G17_ANJUTA_APPLICATION_CLASS(klass)     (G_TYPE_CHECK_CLASS_CAST ((klass), G17_ANJUTA_TYPE_APPLICATION, G17anjutaClass))
#define G17_ANJUTA_IS_APPLICATION(obj)          (G_TYPE_CHECK_INSTANCE_TYPE ((obj), G17_ANJUTA_TYPE_APPLICATION))
#define G17_ANJUTA_IS_APPLICATION_CLASS(klass)  (G_TYPE_CHECK_CLASS_TYPE ((klass), G17_ANJUTA_TYPE_APPLICATION))
#define G17_ANJUTA_APPLICATION_GET_CLASS(obj)   (G_TYPE_INSTANCE_GET_CLASS ((obj), G17_ANJUTA_TYPE_APPLICATION, G17anjutaClass))

typedef struct _G17anjutaClass G17anjutaClass;
typedef struct _G17anjuta G17anjuta;
typedef struct _G17anjutaPrivate G17anjutaPrivate;

struct _G17anjutaClass
{
	GtkApplicationClass parent_class;
};

struct _G17anjuta
{
	GtkApplication parent_instance;

	G17anjutaPrivate *priv;

};

GType g17_anjuta_get_type (void) G_GNUC_CONST;
G17anjuta *g17_anjuta_new (void);

/* Callbacks */

G_END_DECLS

#endif /* _APPLICATION_H_ */

