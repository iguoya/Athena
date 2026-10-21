#include <iostream>
#include <vector>
#include <tuple>
#include <random>
using namespace std;
template <typename T>

tuple<T, T> find_max_min_gold(vector<T> sample) {
    if(sample.size() > 2) {

        auto mid = sample.size()/2;
        int max1, min1, max2, min2;
        vector<T> part1_sample(sample.begin(), sample.begin()+mid+1);
        vector<T> part2_sample(sample.begin()+mid+1, sample.end());
        tie(max1, min1) = find_max_min_gold(part1_sample);
        tie(max2, min2) = find_max_min_gold(part2_sample);

        if(max2 > max1) max1 = max2;
        if(min1 > min2) min1 = min2;

//        static int divide_times = 1;
//        cout<<"divide times:"<<divide_times<<endl;
//        ++divide_times;

        return make_tuple(max1, min1);
    } else {
        if(sample.size() == 1) {
            return make_tuple(sample.front(), sample.front());
        } else {
            if(sample.front() >= sample.back()) {
                return make_tuple(sample.front(), sample.back());
            } else {
                return make_tuple(sample.back(), sample.front());
            }

        }
    }
}

int main() {
    std::cout << "Hello, World!" << std::endl;
    vector<int> sample;
    default_random_engine e(time(NULL));
    uniform_int_distribution<int> u(1, 10000);
    for(auto i = 0; i < 1000; ++i) {
        sample.push_back(u(e));
    }

    int max, min;
    tie(max, min) = find_max_min_gold(sample);
    cout<<"max:"<<max<<"\t min:"<<min<<endl;
    return 0;
}
