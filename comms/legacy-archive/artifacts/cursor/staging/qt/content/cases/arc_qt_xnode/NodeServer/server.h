#ifndef SERVER_H
#define SERVER_H
#include<stdio.h>
#include<stdlib.h>
#include<unistd.h>
#include<errno.h>
#include<sys/types.h>
#include<sys/socket.h>
#include<netinet/in.h>
#include<string.h>

class Server
{
public:
    Server();
    void listen(uint16_t port);
    void run();
    ~Server();

private:
    int m_socket;
    struct sockaddr_in m_serverAddress;
    struct sockaddr_in m_peerAddress;
};

#endif // SERVER_H
