#include <iostream>
#include "client.h"

using namespace std;


int main(int argc, char *argv[])
{
    Client client(argv[3]);
    client.connect(argv[1], atoi(argv[2]));

    cout<<"客户端"<<argv[3]<<"启动...."<<endl;
    client.run();

    return 0;
}
