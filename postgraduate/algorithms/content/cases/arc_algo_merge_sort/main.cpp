#include <iostream>
#include <vector>
#include <algorithm>
#include <random>

using namespace std;

int main() {
    std::cout << "Hello, World!" << std::endl;
    vector<int> sample(100);
//    default_random_engine e(random_device{}());
    default_random_engine e(random_device{}());
    uniform_int_distribution<unsigned> u(1, 1000);
    for_each(sample.begin(), sample.end(),  [](const int& val){ cout << val << "\t"; });
    for(auto &m: sample) {
        m = u(e);
        cout<<m<<"\t";
    }
    //
    cout<<endl;

    //dddddddd

//    shuffle(sample.begin(), sample.end(), std::default_random_engine(0));
//

    cout<<endl;
    for_each(sample.cbegin(), sample.cend(),  [](const int& val){cout << val << "\t"; });
    cout<<endl;
    return 0;
}
