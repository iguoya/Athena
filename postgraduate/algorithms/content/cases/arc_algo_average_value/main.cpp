#include <iostream>
#include <random>
#include <ctime>
#include <list>

using namespace std;

//int average_value()
int summation(int n) {
    if(n == 1) {
        return 1;
    } else {
        return summation(n-1) + n;
    }
}

int factorial(int n) {
    if(n == 1) {
        return 1;
    } else {
        return factorial(n-1)*n;
    }
}


int main() {
    std::cout << "Hello, World!" << std::endl;

//    default_random_engine e(time(NULL));
//    uniform_int_distribution<int> u(1, 10000);
    cout<< summation(10)<<endl;
    cout<< factorial(10)<<endl;
    list<int> sample = {1, 2, 3, 4, 5, 6, 7};
    sample.remove(5);
    for(auto m: sample) {
        cout<<m<<"\t";
    }
    cout<<endl;


    auto it = sample.begin();
    for(auto i=0; i != sample.size(); ++i) {

        if (i == 2 || i == 3) {
            auto tmp = it;
            ++it;
            sample.erase(it);
        } else {
            ++it;
        }

    }


//            auto tmp_it = ++it;

//            it = tmp_it;
//            cout<<"ddd";
//            break;


    for(auto m: sample) {
        cout<<m<<"\t";
    }

    cout<<endl;

    return 0;
}
