#include "server.h"

Server::Server()
{
    m_socket = socket(PF_INET, SOCK_DGRAM, 0);

}

void Server::listen(uint16_t port)
{
    m_address.sin_family = AF_INET;
    m_address.sin_addr.s_addr = htonl(INADDR_ANY);
    m_address.sin_port = htons(port);

    char msg[30] = {0};
    sprintf(msg, "监听 %d 端口 .....\n", port);
    cout<< msg;
    bind(m_socket, (struct sockaddr *)&m_address, sizeof(m_address));
}

void Server::run()
{

    while(1) {
        struct sockaddr_in client_address;
        char buffer[1024] = {0};  //接收缓冲区，1024字节
        size_t buffer_length = sizeof(buffer);
        socklen_t length = sizeof(client_address);
        int count = recvfrom(m_socket, buffer, buffer_length, 0, (struct sockaddr*)&client_address, &length);  //recvfrom是拥塞函数，没有数据就一直拥塞

        printf("client receive:%s\n",buffer);  //打印client发过来的信息
        memset(buffer, 0, buffer_length);
        sprintf(buffer, "server: I have recieved %d bytes data!\n", count);  //回复client
        printf("server response:%s\n", buffer);  //打印自己发送的信息给
        sendto(m_socket, buffer, buffer_length, 0, (struct sockaddr*)&client_address, length);  //发送信息给client，注意使用了clent_addr结构体指针
    }

//    while (1) {
//        char recvbuf[1024] = {0};
//        socklen_t peerLen = sizeof(m_peerAddress);

//        int n = recvfrom(m_socket, recvbuf, sizeof(recvbuf), 0,
//                         (struct sockaddr *)&m_peerAddress, &peerLen);

//        sendto(m_socket, recvbuf, n, 0,
//               (struct sockaddr *)&m_peerAddress, peerLen);

//    }
}

Server::~Server()
{
    close(m_socket);
}

