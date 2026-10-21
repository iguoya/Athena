#ifndef SINGLETON_H
#define SINGLETON_H

//#include <iostream>
using namespace std;
class Singleton{
    public:
    static Singleton* Instance();
    protected:
    Singleton();
    private:
    static Singleton* _instance;
};

#endif // SINGLETON_H
