//
// Created by tiger on 18-12-6.
//

#ifndef ITERATIVE_COMMON_MULTIPLE_DIVISOR_H
#define ITERATIVE_COMMON_MULTIPLE_DIVISOR_H

//公约数 公倍数

void common_multiple_divisor(int x, int y) {
    //21 14

    int dividend = x > y ? x : y;
    int divisor = x < y ? x : y;
    while (divisor != 0) {
        int tmp = divisor;
        divisor = dividend % divisor;
        dividend = tmp;
    }
//    printf("\n", dividend);
    printf("%d, %d的最大公约数:%d, 最小公约数:%d\n", x, y, dividend, x*y/dividend);

}

#endif //ITERATIVE_COMMON_MULTIPLE_DIVISOR_H
