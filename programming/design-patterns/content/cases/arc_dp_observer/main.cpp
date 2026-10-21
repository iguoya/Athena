#include "subject.h"
#include "observer.h"
#include <iostream>
#include <fstream>
using namespace std;
int main(){
    ConcreteSubject* sub = new ConcreteSubject();
    Observer* o1 = new ConcreteObserverA(sub);
    Observer* o2 = new ConcreteObserverB(sub);
    sub->SetState("old");
    sub->Notify();
    sub->SetState("new"); //也可以由 Observer 调用
    sub->Notify();

//    char buffer[256];
//    ifstream in("explanation.txt");
//    while (!in.eof() )
//    {
//        in.getline (buffer,100);
//        cout << buffer << endl;
//    }
//    in.close();
    //    ofstream out("explanation.txt");
    //    out<<"完全ojbk";
    //    out.close();
    return 0;
}
