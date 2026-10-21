#ifndef LINEAR_H
#define LINEAR_H


#include <cstddef>
template <class T>
class Linear {
private:
    T* _begin;
    T* _end;
    size_t _capacity;
public:
    Linear() {
        _begin = _end = NULL;
        _capacity = 0;
    }


    T * begin() {
        return _begin;
    }
    T* end() {
        return _end;
    }

    size_t capacity() {
        return _capacity;
    }
    size_t size() {
        return _end-_begin;
    }
    bool empty() {
        return (size() == 0)? true: false;
    }

    bool full() {
        return (size() == capacity()) ? true:false;
    }

    void copy(T* _begin, T* _end, T* new_begin) {
        while(_begin != _end) {
            *new_begin = *_begin;
            ++_begin;
            ++new_begin;
        }
    }

    void push_back(const T &e) {
        if(full()) {
            if(capacity() == 0) {
                _capacity = 1;
                _begin = _end = new T;
            } else {
                _capacity *= 2;
                T* new_begin  = new T(_capacity);
                copy(_begin, _end, new_begin);
                _end = new_begin+size();
                delete _begin;
                _begin = new_begin;
            }
        }
        *_end = e;
        ++_end;
    }
    T at(size_t index) {
        return *(_begin+index-1);
    }

    ~Linear() {
        delete _begin;
    }
    //    bool clear() {
    //        Linear.clear();
    //        if(Linear.Empty() == 0) {
    //            return true;
    //        } else {
    //            return false;
    //        }
    //    }

    //    size_t LocateElem(T e) {
    //        for(size_t i = 1; i < Linear.size(); ++i) {
    //            if(e == Linear.at(i)) {
    //                return i;
    //            }
    //        }
    //        return 0;
    //    }

};


#endif // LINEAR_H
