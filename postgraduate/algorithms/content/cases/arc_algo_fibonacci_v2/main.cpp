#include <iostream>
#include <vector>
using namespace std;

void fibonacci(int n, vector<int> &result) {
    if(n>2) {
        fibonacci(n-1, result);
        int first_num = result[result.size()-1];
        int second_num = result[result.size()-2];
        result.push_back(first_num+second_num);
    } else {
        if(n == 1) {
            result.push_back(1);
        } else if(n == 2){
            result.push_back(1);
            result.push_back(1);
        }
    }

}
int main() {
    std::cout << "Hello, World!" << std::endl;
    vector<int> result;
    fibonacci(20, result);
    for (const auto it : result){
        cout<<it<<"\t";
    }
    cout<<endl;

    return 0;
}
