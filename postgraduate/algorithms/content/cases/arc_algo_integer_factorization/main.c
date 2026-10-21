//
// Created by tiger on 18-12-7.
//

#include <stdio.h>

void integer_factorization(int n) {
    static int factor_arr[100];
    static int index;
    static int total_sum;
    if(n == 0) {
        printf("%3d\t\t:", ++total_sum);
        for(int i = 0; i < index; ++i) {
            printf("%d\t", factor_arr[i]);
        }
        printf("\n");
    } else {
        for(int factor = 1; factor <= n; ++factor) {
            factor_arr[index] = factor;
            ++index;
            integer_factorization(n-factor);
            --index;
        }
    }
}
int main() {
    printf("-------整数分解--------\n");
    integer_factorization(10);
}


