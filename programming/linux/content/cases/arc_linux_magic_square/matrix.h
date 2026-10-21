//
// Created by tiger on 18-10-24.
//

#ifndef MAGIC_SQUARE_MATRIX_H
#define MAGIC_SQUARE_MATRIX_H
typedef struct coords {
    int x;
    int y;
} coords;


typedef struct node {
    int value;
    int row;
    int column;
} node;

int get_avg_sum(int n);

coords *get_slash_coords(int n);


node *init_matrix(int n);

void show_matrix(node *p, int n);

node *get_slash_node(int n);

coords *hex_convert(int num, int *degree_num, int n);

void show_coords(coords *p, int n);

void test(int n);

#endif //MAGIC_SQUARE_MATRIX_H