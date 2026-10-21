#ifndef SERVERNODE_H
#define SERVERNODE_H

#include <stdint.h>
#include <string>
using namespace std;

class ServerNode
{
public:
    ServerNode();
    ServerNode(string ip, uint16_t port): ip(ip), port(port){};


//private:

    string ip;
    uint16_t port;

};

#endif // SERVERNODE_H
