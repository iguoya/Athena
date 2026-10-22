/* -*- Mode: C; indent-tabs-mode: t; c-basic-offset: 4; tab-width: 4 -*-  */
/*
 * g29-grid.h
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

#ifndef _G29_GRID_
#define _G29_GRID_

#include <gtk/gtk.h>

G_BEGIN_DECLS

#define G29_GRID_TYPE_APPLICATION             (g29_grid_get_type ())
#define G29_GRID_APPLICATION(obj)             (G_TYPE_CHECK_INSTANCE_CAST ((obj), G29_GRID_TYPE_APPLICATION, G29grid))
#define G29_GRID_APPLICATION_CLASS(klass)     (G_TYPE_CHECK_CLASS_CAST ((klass), G29_GRID_TYPE_APPLICATION, G29gridClass))
#define G29_GRID_IS_APPLICATION(obj)          (G_TYPE_CHECK_INSTANCE_TYPE ((obj), G29_GRID_TYPE_APPLICATION))
#define G29_GRID_IS_APPLICATION_CLASS(klass)  (G_TYPE_CHECK_CLASS_TYPE ((klass), G29_GRID_TYPE_APPLICATION))
#define G29_GRID_APPLICATION_GET_CLASS(obj)   (G_TYPE_INSTANCE_GET_CLASS ((obj), G29_GRID_TYPE_APPLICATION, G29gridClass))

typedef struct _G29gridClass G29gridClass;
typedef struct _G29grid G29grid;
typedef struct _G29gridPrivate G29gridPrivate;

struct _G29gridClass
{
	GtkApplicationClass parent_class;
};

struct _G29grid
{
	GtkApplication parent_instance;

	G29gridPrivate *priv;

};

GType g29_grid_get_type (void) G_GNUC_CONST;
G29grid *g29_grid_new (void);

/* Callbacks */

G_END_DECLS

#endif /* _APPLICATION_H_ */

