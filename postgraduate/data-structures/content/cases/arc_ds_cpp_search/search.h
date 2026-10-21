#ifndef SEARCH_H
#define SEARCH_H

#include <vector>
using namespace std;

template <class T>
class Search {
public:
    vector<T> data;

public:

    size_t sequence(T *e) {
        size_t location = 1;
        for(auto it = data.begin(); it != data.end(); ++it, ++location) {
            if(*it == *e) {
                return location;
            }
        }
        return 0;
    }

    size_t binary_recursion(T *e, size_t begin, size_t end) {
        if(end-begin == 1) {
            if(*e == data.at(begin)) {
                return begin+1;
            }
            if(*e == data.at(end)) {
                return end+1;
            }
            return 0;
        }

        size_t middle = (begin+end)/2;

        if(*e > data.at(middle)) {
            return binary(e , middle, end+1);
        } else if(*e < data.at(middle)) {
            return binary(e , begin, middle);
        } else if(*e == data.at(middle)) {
            return middle+1;// 索引从0开始
        }
        return 0;
    }
    size_t binary(T *e) {
        size_t begin = 0;
        size_t end = data.size()-1;

        while(begin <= end) {
            size_t middle = (begin + end)/2;
            if(*e < data.at(middle)) {
                end = middle - 1;
            } else if(*e > data.at(middle)) {
                begin = middle + 1;
            } else {
                return middle + 1;
            }
        }
        return 0;
    }
};
#endif // SEARCH_H
