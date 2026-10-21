#include <iostream>
#include "Factory.h"
using namespace std;

int main(int argc, char *argv[])
{
    cout << "Hello World!" << endl;

    Factory* fc = new Factory();
    Product *pa = fc->CreateProduct("A");
    Product *pb = fc->CreateProduct("B");
    Product *pc = fc->CreateProduct("C");
    return 0;
}
