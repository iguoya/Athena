#include <stdio.h>
typedef  char StackElemType;
#include "stack.h"

int main() {
    printf("单链表逆序\n");
    LinkStack ls = init_stack();
    push(ls, 'A');
    push(ls, 'B');
    push(ls, 'C');
    push(ls, 'D');
    push(ls, 'E');
    push(ls, 'F');
    push(ls, 'G');
//    char a;
//    while(!empty_stack(ls)) {
//        get_top(ls, &a);
//        pop(ls);
//        printf("%c\t", a);
//    }
//    printf("\n");
    //另一种遍历方法
    LinkStackNode p = *ls;
    while(p != NULL) {
        printf("%c\t", p->value);
        p = p->next;
    }
    printf("\n---------------逆序单链表-------------------\n");
    LinkStackNode pre = *ls;
    LinkStackNode index = pre->next;
    LinkStackNode next = index->next;
    while(index != NULL) {
        if(pre == *ls) {
            pre->next = NULL;
        }
        index->next = pre;
        pre = index;
        index = next;
        if(next) {
            next = next->next;
        }
    }

    p = pre;
    while(p != NULL) {
        printf("%c\t", p->value);
        p = p->next;
    }

    return 0;
}