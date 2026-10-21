#include <stdio.h>
#include <stdlib.h>

#include "matrix.h"


int **get_matrix(int n) {
    int avg_sum = get_avg_sum(n);
    if (avg_sum == -1) return NULL;

    int (*p)[n] = (int (*)[n]) malloc(sizeof(int) * n * n);
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            printf("i:%d, j:%d, %p\t", i, j, &p[i][j]);
            p[i][j] = i * n + j + 1;
        }
        printf("\n");
    }

    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            printf("i:%d, j:%d, %d\t", i, j, p[i][j]);
        }
        printf("\n");
    }
    free(p);
    return NULL;
}

int main() {
    printf("Hello, World!\n");
    for(int n = 2; n < 5; ++n) {
        printf("\n---------------------------\n");
        struct node *p = init_matrix(n);
        show_matrix(p, n);
        printf("%d\n", get_avg_sum(n));
        get_matrix(n);
        test(n);
    }
    return 0;
}