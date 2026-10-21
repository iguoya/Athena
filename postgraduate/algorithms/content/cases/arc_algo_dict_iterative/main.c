#include <stdio.h>
#include <math.h>

#include "common_multiple_divisor.h"
#include "factorization.h"
#include "sqrt.h"


int main() {
    common_multiple_divisor(100, 20);
    common_multiple_divisor(23, 13);
    common_multiple_divisor(25, 15);
    common_multiple_divisor(22, 21);
    common_multiple_divisor(14, 21);
    factorization(100);
    factorization(54);
    factorization(54);
    factorization(8192);

    my_sqrt(5);
    my_sqrt(100);
    my_sqrt(300);
    return 0;
}