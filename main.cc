#include "athena.h"

#include <gtksourceview/gtksource.h>

int main(int argc, char* argv[]) {
  gtk_source_init();
  int status = 0;
  {
    auto app = Athena::create();
    status = app->run(argc, argv);
  }
  gtk_source_finalize();
  return status;
}
