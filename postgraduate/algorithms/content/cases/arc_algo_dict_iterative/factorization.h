//
// Created by tiger on 18-12-6.
//

#ifndef ITERATIVE_FACTORIZATION_H
#define ITERATIVE_FACTORIZATION_H


//质因数分解

void factorization(int n) {
    printf("因数分解:%d = ", n);
    while(n != 1) {
        for(int i = 2; i <= n; ++i) {
            if(n%i == 0) {
                printf("%d*", i);
                n /= i;
                break;
            }
        }
    }
    printf("\n");
}

#endif //ITERATIVE_FACTORIZATION_H
