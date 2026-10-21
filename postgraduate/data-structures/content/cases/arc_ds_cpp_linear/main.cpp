#include <iostream>
#include "list.h"
using namespace std;
void Jesephus(int amount = 39) {
    List<int> jesephus;
    for(int i = 1; i <= amount; ++i) {
        jesephus.push_back(i);
    }

    jesephus.end()->next = jesephus.begin();
//    for(auto it = jesephus.begin(); it != jesephus.end(); it= it->next) {
//        cout<<it->data<<"\t";
//    }
    auto mark = jesephus.begin();
    auto remove = jesephus.begin();
    int times = 1;
    while(times <= amount) {
        for(int i = 1; i <= 2; ++i) {
            mark = mark->next;
        }
        remove = mark;
        cout<<remove->data<<"\t";
        //        if(times % 5 == 0) cout<<endl;
        //if(mark == NULL) break;
        mark = jesephus.erase(remove);
        cout<<"time:"<<times<<"\t"
           <<"me:"<<mark<<"\t"
          <<"before:"<<mark->prior<<"\t"
         <<"\tafter:"<<mark->next<<endl;
        ++times;
    }
}

void Magician(int amount = 13) {
    List<int> poker;
    for(int i = 1; i <= amount; ++i) {
        poker.push_back(i);
    }

        for(auto it = poker.begin(); it != poker.end(); it= it->next) {
            cout<<it->data<<"\t";
        }

//    poker.end()->next = poker.begin();
//    auto mark = poker.begin();
//    auto remove = poker.begin();
//    int times = 1;
//    while(times <= amount) {
//        for(int i = 1; i < times; ++i) {
//            mark = mark->next;
//        }
//        remove = mark;
//        cout<<remove->data<<"\t";
//        //        if(times % 5 == 0) cout<<endl;
//        //if(mark == NULL) break;
//        mark = poker.erase(remove);
//        cout<<"time:"<<times<<"\t"
//          <<"before:"<<mark->prior<<"\t"
//         <<"\tafter:"<<mark->next<<endl;
//        ++times;
//    }

}
int main()
{
    cout << "Hello World!" << endl;
    cout<<"出圈问题"<<endl;
    Jesephus();
    cout<<"发牌问题"<<endl;
    Magician(13);
    return 0;
}
