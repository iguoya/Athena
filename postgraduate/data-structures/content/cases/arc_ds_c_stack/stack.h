//
// Created by tiger on 18-11-1.
//
#include <stdlib.h>
#include <stdbool.h>

#ifndef STACK_STACK_H
#define STACK_STACK_H

typedef struct StackNode{
    struct StackNode *next;
    StackElemType value;
} StackNode, *LinkStackNode;

typedef LinkStackNode * LinkStack;

//LinkStack init_stack();
//bool empty_stack(LinkStack top);
//
//void push(LinkStack top, StackElemType e);
//bool pop(LinkStack top);
//bool get_top(LinkStack top, StackElemType *e);


LinkStack init_stack() {
    LinkStack p = malloc(sizeof(LinkStackNode));
    *p = NULL;
    return p;
}

bool empty_stack(LinkStack top) {
    if((*top) == NULL) {
        return true;
    } else {
        return false;
    }
}

void push(LinkStack top, StackElemType value) {
    LinkStackNode p = malloc(sizeof(StackNode));
    p->value = value;
    p->next = (*top);
    *top = p;
}

bool pop(LinkStack top) {
    if(empty_stack(top)) {
        return false;
    } else {
        LinkStackNode p = *top;
        (*top) = (*top)->next;
        free(p);
        return true;
    }
}

bool get_top(LinkStack top, StackElemType *e) {
    if(empty_stack(top)) {
        return false;
    } else {
        *e = (*top)->value;
        return true;
    }
}

#endif //STACK_STACK_H
