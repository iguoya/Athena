#include "server.h"


int main(int argc, char* argv[])
{

    Server server;

    server.listen(atoi(argv[1]));

    server.run();


    return 0;
}
