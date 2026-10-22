#include "tiger.h"
#include <iostream>

Tiger::Tiger(QObject *parent) : QObject(parent)
{

}

void Tiger::work()
{
    std::cout<<"work !!!"<<std::endl;
}

void Tiger::testHello()
{
    std::cout<<"hello world !!!"<<std::endl;

}
