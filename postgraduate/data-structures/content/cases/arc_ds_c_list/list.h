//
// Created by tiger on 18-11-22.
//
#include <stdlib.h>
#include <stdbool.h>


#ifndef LIST_LIST_H
#define LIST_LIST_H

typedef struct ListNode {
    struct ListNode *next;
    ListElemType data;
} ListNode , * LinkListNode;

typedef  LinkListNode  List;


typedef struct DListNode {
    struct ListNode *prior;
    struct ListNode *next;
    ListElemType data;
} DListNode , * DLinkListNode;

typedef  DLinkListNode  DList;


List init_list() {
    //带头结点
    List head = malloc(sizeof(ListNode));
    head->next = NULL;
    return head;
}

bool empty_list(List l) {
    if(l->next) {
        return false;
    }
    return true;
}

bool insert_list(List l, size_t index,  ListElemType e) {
    LinkListNode ln = malloc(sizeof(ListNode));
    ln->data = e;

    LinkListNode p = l;
    int i = 1;
    while(i < index) {
        p = p->next;
        ++i;
    }

    if(i != index) {
        return false;
    } else {
        ln->next = p->next;
        p->next = ln;
        return true;
    }
}

typedef void(*Do)(List, ListElemType);

void visit_list(List l, Do operate) {
    for(List lp = l->next; lp != NULL; lp=lp->next) {
//        printf("%d\t", lp->data);
        operate(l, lp->data);
    }
    printf("\n");
}

#endif //LIST_LIST_H
