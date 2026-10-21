#include <stdio.h>
#include <stdbool.h>
#include <stdlib.h>

int *find_max() {
    int arr[]= {7, 48, 46, 5, 69, 74, 11, 18, 10, 14,
                72, 5, 99, 1, 6, 73, 71, 25, 44, 42,
                47, 41, 65, 3, 64, 63, 7, 62, 28, 20,
                30, 32, 70, 34, 68, 35, 59, 36, 85, 12,
                89, 52, 100};

    int n = 5;
//    printf("找出前几个大数？\n");
//    scanf("%d", &n);


    int *max_n = malloc(sizeof(int)*n);
    int min_index = 0;
    printf("%d\n", sizeof(arr));

    for(int i = 0; i < sizeof(arr)/sizeof(int); ++i) {
        if(i < n) {
            max_n[i] = arr[i];
        } else {
            //找出最小值的下标
            for(int j = 0; j < n; ++j) {
                if(*(max_n+j) < *(max_n+min_index)) {
                    min_index = j;
                }
            }
            if(arr[i] > max_n[min_index]) {
                *(max_n+min_index) = arr[i];
            }
//            for(int i = 0; i < n; ++i) {
//                printf("%d\t", *(max_n+i));
//            }
//            printf("\n");
        }
    }
    for(int i = 0; i < 5; ++i) {
        printf("%d\t", *(max_n+i));
    }
    printf("\n");
    return max_n;
}

int **matrix_rotation() {
//    const int n = 5;
    int arr[5][5] = {
            {1, 2, 3, 4, 5},
            {6, 7, 8, 9, 10},
            {11, 12, 13, 14, 15},
            {16, 17, 18, 19, 20},
            {21, 22, 23, 24, 25}
    };

    for(int i = 0; i < 5; ++i) {
        for(int j = 0; j < 5; ++j) {
            printf("%d\t", arr[i][j]);
        }
        printf("\n");
    }
    printf("-------\n");
    int rotate_arr[5][5];

    for(int i = 0; i < 5; ++i) {
        for(int j = 0; j < 5; ++j) {
            rotate_arr[j][5-i-1] = arr[i][j];
        }
    }

    for(int i = 0; i < 5; ++i) {
        for(int j = 0; j < 5; ++j) {
            printf("%d\t", rotate_arr[i][j]);
        }
        printf("\n");
    }
    return NULL;
}

void magic_square(int n) {
    int (*magic_square)[n] = (int (*)[n])malloc(sizeof(int)*n*n);
    bool positive_direction = true;
    for(int column = 0; column < n; ++column) {
        for(int row = 0; row < n; ++row) {
            if(positive_direction) {
                magic_square[row][column] = column*n+row+1;
            } else {
                magic_square[n-row-1][column] = column*n+row+1;
            }
        }
        positive_direction = !positive_direction;
    }
    for(int row = 0; row < n; ++row) {
        int sum = 0;
        for(int column = 0; column < n; ++column) {
            printf("%d\t", magic_square[row][column]);
            sum+= magic_square[row][column];
        }
        printf("---->和:%d\n", sum);
    }
}


int main() {

    printf("**********查找前N个最大值*****************\n");
    find_max();
    printf("**********矩阵旋转90度*****************\n");
    matrix_rotation();
    printf("**********幻方*****************\n");
    for(int i = 2; i < 8; i = i+2) {
        printf("\n-------%d阶幻方--------\n", i);
        magic_square(i);
    }




    return 0;
}