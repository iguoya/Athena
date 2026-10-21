#include <stdio.h>

typedef int ListElemType;
typedef int SortElemType;
#include "../list/list.h"
#include "sort.h"

void print(List l, SortElemType e) {
    printf("%d\t", e);
}

int main() {

    int unsort[] = {17, 46, 32, 87, 58, 9, 50, 38, 155, 166,178};
    int len = sizeof(unsort)/sizeof(int);
    printf("Hello, World!%d\n", len);


    List sort = insert_sort(unsort, len);
    visit_list(sort, print);
    printf("\n------冒泡排序----\n");

    visit_sort(bubble_sort(unsort, len), len);

    //
//    printf("\nsize:%d\n", sizeof(s));



    return 0;
}