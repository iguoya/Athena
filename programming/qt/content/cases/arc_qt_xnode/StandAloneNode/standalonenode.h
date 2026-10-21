#ifndef STANDALONENODE_H
#define STANDALONENODE_H
//#include "server.h"
//#include "client.h"

class StandAloneNode
{
public:
    StandAloneNode();

    void setListenPort(uint16_t port);
    void setName(string name);

    void connect(string ip, uint16_t port);

    Server server;
    Client client;
    void run();
};

#endif // STANDALONENODE_H
