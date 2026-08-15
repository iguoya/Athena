#include "application.h"

int main(int argc, char *argv[])
{
    auto app = new Application;
    return app->run(argc, argv);
}
