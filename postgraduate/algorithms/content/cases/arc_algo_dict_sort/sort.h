//
// Created by tiger on 18-11-23.
//
#include <stdlib.h>
#include <stdbool.h>


#include "../list/list.h"

#ifndef SORT_SORT_H
#define SORT_SORT_H

void insert(List l, ListElemType e) {
    int pos = 1;

    if(empty_list(l)) {
        insert_list(l, pos, e);
    } else {
        //排除头结点
        for(List lp = l->next; lp != NULL; lp=lp->next, ++pos) {
            if (lp->next) {
                if(e >= lp->data && e < lp->next->data) {
                    insert_list(l, pos+1, e);
                    break;
                } else {
                    if(e <= lp->data) {
                        insert_list(l, pos, e);
                        break;
                    }
                }
            } else {
                if (e >= lp->data) {
                    insert_list(l, pos + 1, e);
                    break;
                } else {
                    insert_list(l, pos, e);
                    break;
                }
            }
        }
    }
}

List insert_sort(SortElemType *unsort, int len) {

    List sort = init_list();
    for(int i = 0; i < len; ++i) {
        insert(sort, unsort[i]);
    }
    return sort;
}
void exchange(int *a, int *b) {
    int tmp = *a;
    *a = *b;
    *b = tmp;
}
void visit_sort(SortElemType *sort, int len) {
    for(int i = 0; i < len; ++i) {
        printf("%d\t", sort[i]);
    } 
    printf("\n");
}

SortElemType *bubble_sort(SortElemType *unsort, int len) {

    for(int i = 0; i < len; ++i) {
        int flag = 0;

        for(int j = i; j < len; ++j) {
            if(unsort[i] > unsort[j]) {
                exchange(&unsort[i], &unsort[j]);
                flag = 1;
            }
        }
        if(flag == 0) {
            printf("\nover\n");
            break;
        } else {
            visit_sort(unsort, len);
        }
    }
    return unsort;
}

#endif //SORT_SORT_H
