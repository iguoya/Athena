#include <iostream>
#include <vector>
#include <list>
#include <map>
#include <iomanip>
using namespace std;

//template <typename T>
bool check_points(map<int, int> points) {

    for(auto item: points) {
        cout<<"("<<item.first<<","<<item.second<<")"<<"\t";
    }
    cout<<endl;

    for(auto it=points.begin(); it!=points.end(); ++it) {
        int offset = 1;

        auto ip = it;
        ++ip;
        for(; ip != points.end(); ++ip, ++offset) {
//            cout<<"compare:"<<"("<<it->first+offset<<","<<it->second+offset<<") vs"
//            <<"("<<ip->first<<","<<ip->second<<")"
//            <<"\toffset:"<<offset
//            <<endl;

            if(it->second+offset == ip->second) {
//                cout<<"same"<<endl;
                return false;
            }
//            cout<<"compare: "<<"("<<it->first+offset<<","<<it->second-offset<<") vs"
//                <<"("<<ip->first<<","<<ip->second<<")"
//                <<"\toffset:"<<offset
//                <<endl;
            if(it->second-offset == ip->second) {
//                cout<<"same"<<endl;
                return false;
            }
        }

    }
    cout<<"------------succeed-------------"<<endl;
    return true;
}


//template <typename T>
bool check_rule(const vector<int> &route) {
    //check from small to large , sequential
    bool is_less_valid = 0;
    map<int, int> points;
    int row = 1;
    for(const auto node: route) {
        points.insert(make_pair(row, node));
        ++row;
    }
    return check_points(points);
}


//template <typename T>
void queen(list<int> sample, vector<int> route, vector<vector<int>> &result) {
    if(sample.size() == 0) {
        if(check_rule(route)) {
            result.push_back(route);
        }
//        result.push_back(route);
    } else {
        for(const auto node: sample) {
            route.push_back(node);
            list<int> less_sample(sample);
            less_sample.remove(node);
            queen(less_sample, route, result);
            route.pop_back();
        }
    }
}


template <typename T>
void show(vector<vector<T>> &result) {
    for(const auto &route: result) {
        for(const auto &node: route) {
            cout<<node<<"\t";
        }
        cout<<endl;
    }
    cout<<endl;
}

//template <typename T>
void show_chessboard(vector<vector<int>> &result) {
//    cout<<"符合规则的八皇后棋盘共有:\t"<<result.size()<<"\t种";

    for(const auto &route: result) {
        map<int, int> points;
        int row = 1;
        for(const auto &node: route) {
            points.insert(make_pair(row, node));
            ++row;
        }
        for(auto item: points) {
            cout<<"("<<item.first<<","<<item.second<<")"<<"\t";
        }

        cout<<endl;
        int range = route.size();
        for(int x = 1; x<= range; ++x) {
            for(int y = 1; y<=range; ++y) {
                if(points[x] == y) {
                    cout<<setw(2)<<"*";
                } else {
                    cout<<setw(2)<<".";
                }
            }
            cout<<endl;
        }
        cout<<endl;
        cout<<"------------------------";
        cout<<endl;
    }
    cout<<endl;
}

int main() {
    std::cout << "Hello, World!" << std::endl;

//    list<int> sample={1, 2, 3, 4};
    list<int> sample={1, 2, 3, 4, 5, 6, 7, 8};
    vector<int> route;
    vector<vector<int>> result;

    queen(sample, route, result);

    show(result);
    show_chessboard(result);
    cout<<"八皇后棋盘共有:\t"<<result.size()<<"\t种";
    return 0;
}
