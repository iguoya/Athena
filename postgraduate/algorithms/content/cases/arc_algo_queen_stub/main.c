//
// Created by tiger on 18-11-12.
//
#include <stdio.h>

//
//typedef struct Coords {
//    int x;
//    int y;
//} Coords;
//
//typedef Coords DataType;
////#define DataType Coords
//
//#include "../stack/stack.h"
//
//#define N 8
//
//const int limit_times = 100;
//static int times = 0;
//void visit(LinkStack top) {
//    LinkNode p = *top;
//    while(p != NULL) {
//        printf("(%d, %d)\t", p->value.x, p->value.y);
//        p = p->next;
//    }
//    printf("\n");
//}
//
//bool check_valid(LinkStack top, Coords c) {
//    return  true;
//}
//
//void queen(LinkStack top, int x) {
//    if(x > N) {
//        visit(top) ;
//        ++times;
//        if(times > limit_times) {
//            exit(EXIT_SUCCESS);
//        }
//    } else {
//        for (int y = 1; y <= N; ++y) {
//            Coords c = {x, y};
//            if(check_valid(top, c)) {
//                push(top, c);
//                queen(top, x+1);
//            }
//        }
//    }
//}
//
#include <stdbool.h>
#define BLOCK 4

bool check() {
    return true;
}

void queen(int n) {
    int queen[BLOCK][BLOCK] = {};
    for(int row = 0; row < BLOCK; ++row) {
        for(int column = 0; column < BLOCK; ++column) {
            printf("%d\t", queen[row][column]);
        }
        printf("\n");
    }


//    for(int row = 0; row < BLOCK; ++row) {
//        for(int column = 0; column < BLOCK; ++column) {
//            queen[row][column] = 1;
//
//
//
//        }
//    }

}
int main() {
    queen(4);

//    printf("(%d, %d)\n", c.x, c.y);


}

