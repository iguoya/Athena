#ifndef CLIENT_H
#define CLIENT_H


#include <unistd.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <stdlib.h>
#include <stdio.h>
#include <errno.h>
#include <string.h>
#include "NodeLibrary/nodelibrary.h"
#include <string>
#include <vector>
#include <random>
#include <fstream>

using namespace std;

//using std::string;
//using std::random_device;
//using std::default_random_engine;

class Client
{
public:
    Client();
    ~Client();


    void connect(string ip, uint16_t port);
    void run();

    static size_t count;

private:

    string generateMessage();
    void request(string message);
    void response();
    void writeLog(string fileName);

    vector<Log> sendLogs;
    vector<Log> receiveLogs;

    char sendData[1024];
    char receiveData[1024];

    int m_socket;
    struct sockaddr_in m_address;
    struct sockaddr_in server_address;
};

#endif // CLIENT_H
