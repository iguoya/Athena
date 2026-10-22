/* -*- Mode: C; indent-tabs-mode: t; c-basic-offset: 4; tab-width: 4 -*-  */
/*
 * g28-pack.h
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

#ifndef _G28_PACK_
#define _G28_PACK_

#include <gtk/gtk.h>

G_BEGIN_DECLS

#define G28_PACK_TYPE_APPLICATION             (g28_pack_get_type ())
#define G28_PACK_APPLICATION(obj)             (G_TYPE_CHECK_INSTANCE_CAST ((obj), G28_PACK_TYPE_APPLICATION, G28pack))
#define G28_PACK_APPLICATION_CLASS(klass)     (G_TYPE_CHECK_CLASS_CAST ((klass), G28_PACK_TYPE_APPLICATION, G28packClass))
#define G28_PACK_IS_APPLICATION(obj)          (G_TYPE_CHECK_INSTANCE_TYPE ((obj), G28_PACK_TYPE_APPLICATION))
#define G28_PACK_IS_APPLICATION_CLASS(klass)  (G_TYPE_CHECK_CLASS_TYPE ((klass), G28_PACK_TYPE_APPLICATION))
#define G28_PACK_APPLICATION_GET_CLASS(obj)   (G_TYPE_INSTANCE_GET_CLASS ((obj), G28_PACK_TYPE_APPLICATION, G28packClass))

typedef struct _G28packClass G28packClass;
typedef struct _G28pack G28pack;


struct _G28packClass
{
	GtkApplicationClass parent_class;
};

struct _G28pack
{
	GtkApplication parent_instance;

};

GType g28_pack_get_type (void) G_GNUC_CONST;
G28pack *g28_pack_new (void);

/* Callbacks */

G_END_DECLS

#endif /* _APPLICATION_H_ */

