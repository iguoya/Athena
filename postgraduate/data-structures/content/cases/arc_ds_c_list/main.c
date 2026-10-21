#include <stdio.h>
typedef int ListElemType;
#include "list.h"

void print(int e) {
    printf("%d\t", e);
}

int main() {
//    printf("Hello, World!\n");
    List l = init_List();
    insert_list(l, 1, 22);
    insert_list(l, 1, 55);
    insert_list(l, 1, 45);
    insert_list(l, 2, 11);
    visit(l, print);
    return 0;
}