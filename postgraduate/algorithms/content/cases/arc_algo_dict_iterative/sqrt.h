//
// Created by tiger on 18-12-6.
//

#ifndef ITERATIVE_SQRT_H
#define ITERATIVE_SQRT_H

void my_sqrt(double n) {
    double x0 = n/2;
    double x1 = 0;
    while(fabs(x0-x1) > 1e-2) {
        x1 = x0;
        x0 = 1.0/2*(x1+n/x1);
        printf("x0:   %.2f, x1:  %.2f\n", x0, x1);
    }
}

#endif //ITERATIVE_SQRT_H
