#include "server.h"

Server::Server()
{
    m_socket = socket(PF_INET, SOCK_DGRAM, 0);

}

void Server::listen(uint16_t port)
{
    m_serverAddress.sin_family = AF_INET;
    m_serverAddress.sin_addr.s_addr = htonl(INADDR_ANY);
    m_serverAddress.sin_port = htons(port);


    printf("监听%d端口\n", port);
    bind(m_socket, (struct sockaddr *)&m_serverAddress, sizeof(m_serverAddress));
}

void Server::run()
{

    while (1) {
        char recvbuf[1024] = {0};
        socklen_t peerLen = sizeof(m_peerAddress);

        int n = recvfrom(m_socket, recvbuf, sizeof(recvbuf), 0,
                         (struct sockaddr *)&m_peerAddress, &peerLen);

        sendto(m_socket, recvbuf, n, 0,
               (struct sockaddr *)&m_peerAddress, peerLen);

    }
}

Server::~Server()
{
    close(m_socket);
}

