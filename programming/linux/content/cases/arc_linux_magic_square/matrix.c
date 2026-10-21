//
// Created by tiger on 18-10-24.
//
#include "matrix.h"
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <tgmath.h>

node *init_matrix(int n) {
    node *p = (node *) malloc(sizeof(node) * n * n);

    int number = 1;
    bool positive_direction = true;
    int offset = 0;


    for (int column = 1; column <= n; ++column) {
        if (positive_direction) {
            for (int row = 1; row <= n; ++row, ++number) {
                offset = (row - 1) * n + column - 1;
                (p + offset)->value = number;
                (p + offset)->row = row;
                (p + offset)->column = column;
            }
            positive_direction = false;
        } else {
            for (int row = n; row >= 1; --row, ++number) {
                offset = (row - 1) * n + column - 1;
                (p + offset)->value = number;
                (p + offset)->row = row;
                (p + offset)->column = column;
            }
            positive_direction = true;
        }
    }
    return p;
}


void show_matrix(node *p, int n) {
    for (int i = 0; i < n; ++i) {
        int sum = 0;
        for (int j = 0; j < n; ++j) {
            printf("%d(%d,%d)\t", p->value, p->row, p->column);
            sum += p->value;
            ++p;
        }
        printf("\t----\t(和:%d)\n", sum);
    }
}


int get_avg_sum(int n) {
    if (n < 2) return -1;
    int sum = 0;
    for (int i = 1; i <= n * n; ++i) {
        sum += i;
    }
    return sum / n;
}

node *get_slash_node(int n) {
    node *p = (node *) malloc(sizeof(node) * n);
    node *head = p;
    for (int i = 1; i <= n; ++i, ++p) {
        p->column = i;
        p->row = i;
    }
    return head;
}

coords *hex_convert (int num, int *degree_num, int n) {

    coords *p = (coords *)malloc(sizeof(coords)*n);
    coords *head = p;
    for(int i = n-1; i >=0; --i, ++p) {
        p->x = i;
        if(num < *(degree_num+i)) {
            p->y = 0;
        } else {
            p->y = num / *(degree_num+i);
            num = num % *(degree_num+i);
        }
    }
    return head;
}

void show_coords(coords *p, int n) {
    for(int i = 0; i<n; ++i) {
        printf("(%d, %d)\t", p->x, p->y);
    }
    printf("\n");
}

void test(int n) {
    int number_system[n];
    for(int i = 0; i < n; ++i) {
        number_system[i] = pow(n, i);
    }
    for(int possible = 1; possible <=pow(n,n); ++possible) {
        if(possible > 10) break;
        coords *p = hex_convert(possible, number_system, n);
        show_coords(p, n);
    }
}

void generate_formula(node *matrix, int n) {
//    int [n][n];

}
//
//
//void generate_formula(int n) {
//    int sum = get_avg_sum(n);
//
//    int *p = (int *)malloc(sizeof(int)*n*n);
//    int *p_use_times = (int *)malloc(sizeof(int)*n*n);
//    for(int i = 0; i < n*n; ++i) {
//        *(p+i) = i + 1;
//    }
//
//    for(int i = 0; i < n*n; ++i) {
//        *(p_use_times+i) = 0;
//    }
//
//
//    int current_sum = 0;
//    for(int i = 1; i <= n*n; ++i) {
//        current_sum += i;
//
//    }
//}
