#ifndef PARENT_H
#define PARENT_H
#include <iostream>
using namespace std;

class Parent
{
public:
    Parent() {
        parent_public_num = 100;
        parent_private_num = 500;
        parent_protected_num = 800;
    };
    int parent_public_num;
    void public_method(){
        cout<<"public method: num:"<<parent_public_num<<endl;
    };

protected:
    int parent_protected_num;
    void protected_method(){
        cout<<"protected method: num:"<<parent_protected_num<<endl;
    };
private:
    int parent_private_num;
    void private_method(){
        cout<<"private method: num:"<<parent_private_num<<endl;
    };
};

#endif // PARENT_H
