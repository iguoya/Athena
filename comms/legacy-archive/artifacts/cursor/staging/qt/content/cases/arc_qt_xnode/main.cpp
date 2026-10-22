#include <iostream>
#include "xnode.h"
#include <thread>


using namespace std;

int main(int argc, char* argv[])
{
    cout << "Hello World!" << endl;

    XNode node;

    thread server_thread(&XNode::service, &node, atoi(argv[1]));

    server_thread.detach();


    if(argc > 2 && argc <= 4) {
        thread client_thread(&XNode::contact, &node, argv[2], atoi(argv[3]));
        client_thread.detach();
    }


    if(argc > 4 && argc <= 6) {
        thread client_thread(&XNode::contact, &node, argv[4], atoi(argv[5]));
        client_thread.detach();
    }


//    for(const auto &client : node.clients) {
//        thread client_thread(&XNode::contact, &node);
//        client_thread.detach();
//    }



    sleep(600);

//    node.run();

    return 0;
}
