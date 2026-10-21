#ifndef MESSAGE_H
#define MESSAGE_H

#include <stdint.h>
#include <iostream>
#include <string>
#include <chrono>
#include <sys/time.h>
#include <ctime>
using std::string;



class Log
{
public:
    Log(string source, size_t number);

    void setMessage(string message);

//private:
    void setTime();

    size_t number;
//    static size_t count;
    string time;
    string source;
    string destination;
    string message;

};

#endif // MESSAGE_H
