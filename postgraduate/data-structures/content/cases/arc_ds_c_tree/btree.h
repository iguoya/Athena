//
// Created by tiger on 18-11-15.
//

#include <stdlib.h>
#include <stdbool.h>
#include <math.h>
#include <time.h>

#ifndef TREE_BTREE_H
#define TREE_BTREE_H
typedef struct BNode {
    struct BNode *lchild, *rchild;
    TreeElemType data;
} BNode, *Btree;


typedef Btree StackElemType;

typedef Btree QueueElemType;


#include "../stack/stack.h"
#include "../queue/queue.h"


void init_btree(Btree T) {
    T = NULL;
}

void destroy_btree(Btree T) {
//    delete(T);
}


Btree create_btree(TreeElemType e) {
    Btree T = malloc(sizeof(BNode));
    T->lchild = NULL;
    T->rchild = NULL;
    T->data = e;
    return T;
}

bool add_child(Btree T, bool is_lchild, Btree child) {
    if (is_lchild && T->lchild == NULL) {
        T->lchild = child;
        return true;
    } else {
        if (!is_lchild && T->rchild == NULL) {
            T->rchild = child;
            return true;
        }
    }
    return false;
}


void pre_order(Btree T) {
    if (T) {
        visit_tree_node(T->data);
        pre_order(T->lchild);
        pre_order(T->rchild);
    }
}


void normal_pre_order(Btree T) {

    LinkStack right_childs = init_stack();
    Btree cursor = T;
    while (cursor) {
        visit_tree_node(cursor->data);
        if (cursor->rchild) {
            push(right_childs, cursor->rchild);
        }
        if (cursor->lchild) {
            cursor = cursor->lchild;
        } else {
            if (empty_stack(right_childs)) {
                break;
            } else {
                get_top(right_childs, &cursor);
                pop(right_childs);
            }
        }
    }
}


void in_order(Btree T) {
    if (T) {
        in_order(T->lchild);
        visit_tree_node(T->data);
        in_order(T->rchild);
    }
}


void normal_in_order(Btree T) {

    LinkStack retain_childs = init_stack();
    Btree cursor = T;

    //整棵树 节点分类
    while (cursor || !empty_stack(retain_childs)) {
        while(cursor) {
            push(retain_childs, cursor);
            cursor = cursor->lchild;
        }
        if(!empty_stack(retain_childs)) {
            get_top(retain_childs, &cursor);
            visit_tree_node(cursor->data);
            pop(retain_childs);
            cursor = cursor->rchild;
        }
    }
}

size_t get_tree_nodes(Btree T) {

    if(T) {
        size_t left_num = get_tree_nodes(T->lchild);
        size_t right_num = get_tree_nodes(T->rchild);
        return left_num+right_num + 1;
    }
    return 0;
}

size_t get_tree_nodes_2(Btree T, size_t *pn) {
    if(T) {
        ++*pn;
//        printf("%d\t", *pn);
        get_tree_nodes_2(T->lchild, pn);
        get_tree_nodes_2(T->rchild, pn);
    }
}

size_t get_tree_high(Btree T) {
    if(T) {
        size_t left_high = get_tree_high(T->lchild);
        size_t right_high = get_tree_high(T->rchild);
        return left_high > right_high ? left_high +1: right_high +1;
    }
    return 0;
}


size_t get_level_max_num(size_t level) {
    size_t max_num = 0;
    for(size_t i = 1; i <= level; ++i) {
        max_num += pow(2, i-1);
    }
    return max_num;
}
void show_tree_level(TreeElemType e, size_t interval) {
    for(size_t i = 0; i < interval; ++i) {
        printf("\t");
    }
    printf("%c\n", e);
}
void show_tree(Btree T) {
     size_t high = get_tree_high(T);
     size_t max_length = get_level_max_num(high);
     LinkQueue tree_node = init_queue();
     if(T) {
         en_queue(tree_node, T);
     }
     int tree_level = 1;
     while(!empty_queue(tree_node)) {
        show_tree_level(T->data, pow(2, high-tree_level));
        de_queue(tree_node);

        if(T->lchild) {

            en_queue(tree_node, T->lchild);
        }
        if(T->rchild) {
            en_queue(tree_node, T->rchild);
        }
         ++tree_level;
     }
}

void layer_traversal(Btree T) {
    LinkQueue node_queue = init_queue();
    Btree p = T;
    if(p) {
        en_queue(node_queue, p);
    }
    while(!empty_queue(node_queue)) {
        visit_tree_node(p->data);
        de_queue(node_queue);
        if(p->lchild) {
            en_queue(node_queue, p->lchild);
        }
        if(p->rchild) {
            en_queue(node_queue, p->rchild);
        }
    }
}





#endif //TREE_BTREE_H
