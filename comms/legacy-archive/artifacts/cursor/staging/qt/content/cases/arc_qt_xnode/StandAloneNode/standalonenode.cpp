#include "standalonenode.h"

StandAloneNode::StandAloneNode()
{

}

void StandAloneNode::setListenPort(uint16_t port)
{
    server.listen(port);
}

void StandAloneNode::setName(string name)
{
    client.setName(name);
}

void StandAloneNode::connect(string ip, uint16_t port)
{
    client.connect(ip, port);
}

void StandAloneNode::run()
{


//    server.listen(atoi(argv[1]));

//    Client client(argv[3]);
//    client.connect(argv[1], atoi(argv[2]));

//    cout<<"客户端"<<argv[3]<<"启动...."<<endl;
//    client.run();

    client.run();
    server.run();


}
