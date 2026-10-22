/* -*- Mode: C; indent-tabs-mode: t; c-basic-offset: 4; tab-width: 4 -*-  */
/*
 * g32-grid.h
 * Copyright (C) 2022 tiger <tiger@loongnix>
 * 
 * g32-grid is free software: you can redistribute it and/or modify it
 * under the terms of the GNU General Public License as published by the
 * Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * 
 * g32-grid is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License along
 * with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

#ifndef _G32_GRID_
#define _G32_GRID_

#include <gtk/gtk.h>

G_BEGIN_DECLS

#define G32_GRID_TYPE_APPLICATION             (g32_grid_get_type ())
#define G32_GRID_APPLICATION(obj)             (G_TYPE_CHECK_INSTANCE_CAST ((obj), G32_GRID_TYPE_APPLICATION, G32grid))
#define G32_GRID_APPLICATION_CLASS(klass)     (G_TYPE_CHECK_CLASS_CAST ((klass), G32_GRID_TYPE_APPLICATION, G32gridClass))
#define G32_GRID_IS_APPLICATION(obj)          (G_TYPE_CHECK_INSTANCE_TYPE ((obj), G32_GRID_TYPE_APPLICATION))
#define G32_GRID_IS_APPLICATION_CLASS(klass)  (G_TYPE_CHECK_CLASS_TYPE ((klass), G32_GRID_TYPE_APPLICATION))
#define G32_GRID_APPLICATION_GET_CLASS(obj)   (G_TYPE_INSTANCE_GET_CLASS ((obj), G32_GRID_TYPE_APPLICATION, G32gridClass))

typedef struct _G32gridClass G32gridClass;
typedef struct _G32grid G32grid;
typedef struct _G32gridPrivate G32gridPrivate;

struct _G32gridClass
{
	GtkApplicationClass parent_class;
};

struct _G32grid
{
	GtkApplication parent_instance;

	G32gridPrivate *priv;

};

GType g32_grid_get_type (void) G_GNUC_CONST;
G32grid *g32_grid_new (void);

/* Callbacks */

G_END_DECLS

#endif /* _APPLICATION_H_ */

