/* -*- Mode: C; indent-tabs-mode: t; c-basic-offset: 4; tab-width: 4 -*-  */
/*
 * g37-conponent.h
 * Copyright (C) 2022 tiger <tiger@loongnix>
 * 
 * g37-conponent is free software: you can redistribute it and/or modify it
 * under the terms of the GNU General Public License as published by the
 * Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * 
 * g37-conponent is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License along
 * with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

#ifndef _G37_CONPONENT_
#define _G37_CONPONENT_

#include <gtk/gtk.h>

G_BEGIN_DECLS

#define G37_CONPONENT_TYPE_APPLICATION             (g37_conponent_get_type ())
#define G37_CONPONENT_APPLICATION(obj)             (G_TYPE_CHECK_INSTANCE_CAST ((obj), G37_CONPONENT_TYPE_APPLICATION, G37conponent))
#define G37_CONPONENT_APPLICATION_CLASS(klass)     (G_TYPE_CHECK_CLASS_CAST ((klass), G37_CONPONENT_TYPE_APPLICATION, G37conponentClass))
#define G37_CONPONENT_IS_APPLICATION(obj)          (G_TYPE_CHECK_INSTANCE_TYPE ((obj), G37_CONPONENT_TYPE_APPLICATION))
#define G37_CONPONENT_IS_APPLICATION_CLASS(klass)  (G_TYPE_CHECK_CLASS_TYPE ((klass), G37_CONPONENT_TYPE_APPLICATION))
#define G37_CONPONENT_APPLICATION_GET_CLASS(obj)   (G_TYPE_INSTANCE_GET_CLASS ((obj), G37_CONPONENT_TYPE_APPLICATION, G37conponentClass))

typedef struct _G37conponentClass G37conponentClass;
typedef struct _G37conponent G37conponent;
typedef struct _G37conponentPrivate G37conponentPrivate;

struct _G37conponentClass
{
	GtkApplicationClass parent_class;
};

struct _G37conponent
{
	GtkApplication parent_instance;

	G37conponentPrivate *priv;

};

GType g37_conponent_get_type (void) G_GNUC_CONST;
G37conponent *g37_conponent_new (void);

/* Callbacks */

G_END_DECLS
void hello();
#endif /* _APPLICATION_H_ */

