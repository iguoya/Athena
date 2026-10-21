#include <iostream>
#include <vector>
#include <random>
#include <algorithm>

#include <iomanip>

using namespace std;


template <typename T>
int binary_search(const vector<T> &sample,const T item, int begin, int end) {

    if(begin > end) {
        return -1;
    } else {
        int middle_key = begin+(end-begin)/2;
        if(sample[middle_key] == item) {
            return middle_key;
        } else if(sample[middle_key] > item) {
            return binary_search(sample, item, begin, middle_key-1);
        } else {
            return binary_search(sample, item, middle_key+1, end);
        }
    }
}

template <typename T>
void show(const T &sample) {
    for(int i = 1; i <= 100; ++i) {
        cout<<setw(8)<<sample[i-1];
        if(i%10 == 0) {
            cout<<endl;
        }
    }
    cout<<endl;
}
int main() {
    std::cout << "Hello, World!" << std::endl;
    default_random_engine e(0);
    uniform_int_distribution<int> u(1, 10000);
    vector<int> sample;
    for(int i = 0; i< 100; ++i) {
        sample.push_back(u(e));
    }
    show(sample);


    sort(sample.begin(), sample.end(), greater<int>());
    show(sample);

    sort(sample.begin(), sample.end());
    show(sample);




    cout<<binary_search(sample, 4940, 0, sample.size())<<endl;
    cout<<binary_search(sample, 7534, 0, sample.size())<<endl;
    cout<<binary_search(sample, 9999, 0, sample.size())<<endl;
//
//    cout<< setw(4) <<123 <<1234<<endl;
//    cout << 1 <<setw(7) << 1234 << endl;
//    cout << 1 << setw(7) << 1234567891234 << endl;
//    cout << 1 << 1234 << setw(7) << endl;


    return 0;
}
