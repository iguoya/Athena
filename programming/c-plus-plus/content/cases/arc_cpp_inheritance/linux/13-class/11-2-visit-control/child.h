#ifndef CHILD_H
#define CHILD_H



#include "parent.h"
#include <iostream>
using namespace std;

class PublicChild : public Parent
{
public:
    PublicChild() {
        cout<<"Public Parent:"<<endl;;
    };
    void visit_control() {
        cout<<"public:"<<parent_public_num<<endl;
        cout<<"protected:"<<parent_protected_num<<endl;
//        cout<<parent_private_num<<endl;
    }
};



class ProtectedChild : protected Parent
{
public:
    ProtectedChild() {
        cout<<"Protected Parent:"<<endl;;
    };
    void visit_control() {

        cout<<"public:"<<parent_public_num<<endl;
        cout<<"protected:"<<parent_protected_num<<endl;
//        cout<<parent_private_num<<endl;
    };
};


class PrivateChild : private Parent
{
public:
    PrivateChild() {
        cout<<"Private Parent:"<<endl;;
    };
    void visit_control() {

        cout<<"public:"<<parent_public_num<<endl;
        cout<<"protected:"<<parent_protected_num<<endl;
//        cout<<parent_private_num<<endl;
    };
};


#endif // CHILD_H
