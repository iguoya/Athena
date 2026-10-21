#ifndef LIST_H
#define LIST_H


#include <cstddef>
template <class T>
class List
{
private:
    typedef struct node {
        T data;
        struct node *next;
        struct node *prior;
    } node;
    node *_head;
    node *_rear;


public:

    List() {
        _head = NULL;
        _rear = NULL;
    }
    node * begin() {
        return _head;
    }
    node * end() {
        return _rear;
    }
    //    node * operator ++(node *p) {
    //        return p->next;
    //    }
    size_t size() {
        if(_head == _rear && _head == NULL) {
            return 0;
        } else {
            size_t i = 1;
            for(auto it = begin(); it != end(); it = it->next) {
                ++i;
            }
            return i;
        }
    }
    bool empty() {
        if(_head == _rear && _head == NULL) {
            return true;
        } else {
            return false;
        }
    }

    void push_back(const T &e) {
        if(empty()) {
            _head = new node;
            _head->data = e;
            _head->prior = NULL;
            _head->next = NULL;
            _rear = _head;
        } else {
            node *new_node = new node;
            new_node->data = e;
            new_node->prior = _rear;
            new_node->next = NULL;
            _rear->next = new_node;
            _rear = new_node;
        }
    }
    node * erase(node *p) {
        if(p == NULL) return NULL;
        node *prior = p->prior;
        node *next = p->next;
        if(prior != NULL) {
            prior->next = next;
        } else {
            _head = next;
        }
        if(next != NULL) {
            next->prior = prior;
        } else {
            _rear = prior;
        }
        delete p;
        return next;
    }
};

#endif // LIST_H
