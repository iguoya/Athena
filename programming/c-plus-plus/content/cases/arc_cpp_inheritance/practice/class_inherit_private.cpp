#include<iostream>
#include<assert.h>
using namespace std;
class A{
public:
  int a;
  A(){
    public_variate = 1;
    protected_variate = 2;
    private_variate = 3;
    a = 4;
  }
  void fun(){
    cout << a << endl;    //正确
    cout << public_variate << endl;   //正确
    cout << protected_variate << endl;   //正确
    cout << private_variate << endl;   //正确
  }
public:
  int public_variate;
protected:
  int protected_variate;
private:
  int private_variate;
};
class B : private A{
public:
  int a;
  B(int i){
    A();
    a = i;
  }
  void fun(){
    cout << a << endl;       //正确，public成员。
    cout << public_variate << endl;       //正确，基类public成员,在派生类中变成了private,可以被派生类访问。
    cout << protected_variate << endl;       //正确，基类的protected成员，在派生类中变成了private,可以被派生类访问。
    // cout << private_variate << endl;       //错误，基类的private成员不能被派生类访问。
  }
      int add() {
      return public_variate+protected_variate;
  }
};
int main(){
  B b(10);
  cout << b.a << endl;       //正确。public成员
//   cout << b.public_variate << endl;      //错误，private成员不能在类外访问。
//   cout << b.protected_variate << endl;      //错误, private成员不能在类外访问。
//   cout << b.private_variate << endl;      //错误，private成员不能在类外访问。
  cout << "求和:" << b.add() << endl;
  return 0;
}