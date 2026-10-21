#include <iostream>

#include "child.h"


using namespace std;

int main()
{
    cout << "Hello World!" << endl;
    PublicChild cp;
    cout<<cp.parent_public_num<<endl;
    cp.public_method();



    ProtectedChild cr;
//    cout<<cr.parent_public_num<<endl;//保护继承 改变父类公共变量为 保护成员
//    cr.parent_protected_num<<endl; ////保护继承 改变父类 保护变量 为 保护成员
    cr.visit_control();


    PrivateChild ci;
//    cout<< ci.parent_public_num<<endl;// 私有继承 改变父类公共变量为  私有成员
//    cout<< ci.parent_protected_num<<endl;// 私有继承 改变父类保护变量为  私有成员
    ci.visit_control();






    return 0;
}
