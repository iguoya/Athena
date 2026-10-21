#ifndef XNODE_H
#define XNODE_H

#include "server.h"
#include "client.h"

using namespace std;

class XNode
{
public:
    XNode();
    ~XNode();

    void run();

    void service(uint16_t port);

    void contact(string ip, uint16_t port);


//    vector<Client> clients;
private:

    Server server;
    Client client;

    string name;

};

#endif // XNODE_H
