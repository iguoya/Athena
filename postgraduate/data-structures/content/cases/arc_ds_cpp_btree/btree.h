#ifndef BTREE_H
#define BTREE_H

#include <iostream>
#include <iomanip>
#include <vector>
#include <stack>
#include <queue>
#include <random>
#include <functional>
#include <cmath>

using namespace std;
template <class T>
class BtreeNode {
    //二叉链表,无parent
public:
    T *data;
    BtreeNode *lchild;
    BtreeNode *rchild;

    BtreeNode(T *e) {
        data = e;
        lchild = nullptr;
        rchild = nullptr;
    }
    void add_lchild(BtreeNode *lchild) {
        this->lchild = lchild;
    }
    void add_rchild(BtreeNode *rchild) {
        this->rchild = rchild;
    }
    void add_child(BtreeNode *lchild = nullptr, BtreeNode *rchild = nullptr) {
        this->lchild = lchild;
        this->rchild = rchild;
    }
};

template <class T>
class Btree
{
    //private:
public:
    BtreeNode<T> *root;
    Btree() {
        root = nullptr;
    }
    Btree(BtreeNode<T> *root) {
        this->root = root;
    }

    void set_random_tree(size_t nodes = 50, double ratio = 0.80) {

        if(ratio > 1) {//比例必须是小数
            ratio = 1/ratio;
        }

        std::random_device rd;
        std::mt19937 mt(rd());
        std::uniform_int_distribution<int> dist(1, 100);//子树稀疏度
        auto dice = std::bind(dist, mt);

//        for (int i = 0; i < 100; i++) {
//            std::cout << dice() << std::endl;
//        }

        size_t index = 1;
        root = new BtreeNode<size_t>(new size_t(index));
        queue<BtreeNode<size_t> *> node_queue;
        node_queue.push(root);


        while(!node_queue.empty()) {
            if(index >= nodes) {
                break;
            }
            auto node = node_queue.front();

            if(dice() <= ratio*100) {
                node->lchild = new BtreeNode<size_t>(new size_t(++index));
                node_queue.push(node->lchild);
            }
            if(dice() <= ratio*100) {
                node->rchild = new BtreeNode<size_t>(new size_t(++index));
                node_queue.push(node->rchild);
            }
            node_queue.pop();
        }
    }
    void set_full_tree(size_t high = 4) {
        root = new BtreeNode<size_t>(new size_t(1));
        queue<BtreeNode<size_t> *> node_queue;
        node_queue.push(root);
        size_t node_limit = pow(2, high) -1;
        size_t index = 1;
        bool is_left = true;
        while(index < node_limit) {
            auto node = node_queue.front();
            node->lchild = new BtreeNode<size_t> (new size_t(++index));
            node->rchild = new BtreeNode<size_t> (new size_t(++index));
            node_queue.push(node->lchild);
            node_queue.push(node->rchild);
            node_queue.pop();
        }
    }

    size_t depth(BtreeNode<T> *root) {
        if(root) {
            size_t left = depth(root->lchild);
            size_t right = depth(root->rchild);
            return left > right ? left+1 : right+1;
        } else {
            return 0;
        }
    }


    void DLR(BtreeNode<T> *root, vector<T> &result) {
        if(root) {
            result.push_back(*(root->data));
            DLR(root->lchild, result);
            DLR(root->rchild, result);
        }
    }
    vector<T> DLRTraverse() {
        BtreeNode<T> *p = root;
        vector<T> result;
        stack<BtreeNode<T> *> right_children;
        while(p) {
            result.push_back(*(p->data));
            if(p->rchild) {
                right_children.push(p->rchild);
            }
            if(p->lchild) {
                p = p->lchild;
            } else {
                if(!right_children.empty()) {
                    p = right_children.top();
                    right_children.pop();
                } else {
                    p = nullptr;
                }
            }
        }
        return result;
    }

    void LDR(BtreeNode<T> *root, vector<T> &result) {
        if(root) {
            LDR(root->lchild, result);
            result.push_back(*(root->data));
            LDR(root->rchild, result);
        }
    }
    vector<T> LDRTraverse() {
        BtreeNode<T> *p = root;
        vector<T> result;
        stack<BtreeNode<T> *> right_children;
        stack<BtreeNode<T> *> parent;
        while(p) {
            if(p->rchild) {
                right_children.push(p->rchild);
            }
            if(p->lchild) {
                parent.push(p);
                p = p->lchild;
            } else {
                result.push_back(*(p->data));
                if(!parent.empty()) {
                    p = parent.top();
                    result.push_back(*(p->data));
                    parent.pop();
                } else {
                    p = nullptr;
                }
                if(!right_children.empty()) {
                    p = right_children.top();
                    right_children.pop();
                }
            }
        }
        return result;
    }
    void LRD(BtreeNode<T> *root, vector<T> &result) {
        if(root) {
            LRD(root->lchild, result);
            LRD(root->rchild, result);
            result.push_back(*(root->data));
        }
    }
    vector<T> LevelTraverse() {
        vector<T> result;
        if(root) {
            queue<BtreeNode<T> *> node_queue;
            node_queue.push(root);
            while(!node_queue.empty()) {
                BtreeNode<T> *node = node_queue.front();
                if(node->lchild) {
                    node_queue.push(node->lchild);
                }
                if(node->rchild) {
                    node_queue.push(node->rchild);
                }
                result.push_back(*(node->data));
                node_queue.pop();
            }
        }
        return result;
    }
    void show() {
        if(root) {
            queue<BtreeNode<T> *> node_queue;
            node_queue.push(root);

            size_t high = depth(root);
            cout<<"high:"<<high<<endl;
            size_t level = 1;
            size_t children = 0;
            size_t limit_children = pow(2, level);
            bool has_children = false;
            bool is_level_begin = true;
            size_t begin_space = pow(2, high-level)-1;
            size_t interval_space = pow(2, high-level+1)-1;

            while(!node_queue.empty()) {
                BtreeNode<T> *node = node_queue.front();
                if(is_level_begin) {
                    for(size_t i = 1; i <= begin_space; ++i) {
                        //                        cout<<"*";
                        cout<<"  ";
                    }
                    is_level_begin = false;
                } else {
                    //非该层第一个孩子，输出间隔
                    for(size_t i = 1; i <= interval_space; ++i) {
                        //                        cout<<"#";
                        cout<<"  ";
                    }
                }
                if(node) {
                    cout<<setfill(' ')<<setw(2)<<*(node->data);
                    if(node->lchild) {
                        node_queue.push(node->lchild);
                        if(has_children == false) {
                            has_children = true;
                        }
                    } else {
                        node_queue.push(nullptr);
                    }
                    ++children;
                    if(node->rchild) {
                        node_queue.push(node->rchild);
                        if(has_children == false) {
                            has_children = true;
                        }
                    } else {
                        node_queue.push(nullptr);
                    }
                    ++children;
                } else {
                    cout<<"_";// 节点为空
                    node_queue.push(nullptr);
                    ++children;
                    node_queue.push(nullptr);
                    ++children;
                }
                if(children == limit_children) {
                    //                    cout<<"<-----"<<"第"<<level<<"层";
                    cout<<endl;
                    ++level;
                    limit_children = pow(2, level);
                    children = 0;
                    //输出美化，定义每行间隔
                    is_level_begin = true;
                    begin_space = pow(2, high-level)-1;
                    interval_space = pow(2, high-level+1)-1;

                    if(has_children) {
                        has_children = false;
                    } else {
                        break;//节点全部没有孩子，退出
                    }
                }
                node_queue.pop();
            }
        }
    }
};

#endif // BTREE_H
