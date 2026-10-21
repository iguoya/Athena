#include <iostream>
#include <random>
#include <ctime>

using namespace std;

int max_value(int max, vector<int> &assemble) {
    if(assemble.size() == 1) {
        return max > assemble.front() ? max:assemble.front();
    } else {
        int min = assemble.back();
        assemble.pop_back();
        if(max < min) {
            max = min;
        }
        return max_value(max, assemble);
    }

}

int main() {
    std::cout << "Hello, World!" << std::endl;

    default_random_engine e(time(NULL));
    uniform_int_distribution<int> u(1, 10000);
    vector<int> assemble;
    for(int i = 0; i< 100; ++i) {
        assemble.push_back(u(e));

    }
    for(int i = 1; i<= 100; ++i) {
        cout<<assemble[i-1]<<"\t";
        if(i%10 == 0) {
            cout<<endl;
        }
    }

    cout<<"max value:"
    <<max_value(0, assemble)
    <<endl;

    return 0;
}
