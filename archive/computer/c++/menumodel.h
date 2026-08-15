#ifndef MENUMODEL_H
#define MENUMODEL_H

#include <gtkmm.h>
#include <vector>
#include "identifier.h"

using namespace std;
using namespace Glib;



class ModelColumns : public Gtk::TreeModel::ColumnRecord {
public:
  ModelColumns();

  Gtk::TreeModelColumn<ustring> name;
  Gtk::TreeModelColumn<ustring> identifier;
  Gtk::TreeModelColumn<ustring> description;
  //        Gtk::TreeModelColumn<uint8_t> priority;
};

class MenuModel {
public:
  MenuModel();
  RefPtr<Gtk::TreeStore> model;

private:
  using MenuNode = struct {
    ustring name;
    ustring identifier;
    ustring description;
  };
};

#endif // MENU_H
