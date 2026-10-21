#include "xnode.h"

XNode::XNode()
{

}

XNode::~XNode()
{

}


void XNode::run()
{

    //    bind(server_fd, (struct sockaddr*)&server_address, sizeof(server_address));
    //    handleMessage(server_fd);//处理接收到的数据



}


void XNode::service(uint16_t port)
{
    server.listen(port);
    server.run();
}



void XNode::contact(string ip, uint16_t port)
{
    client.connect(ip, port);
    client.run();
}
