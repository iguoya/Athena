#include <stdio.h>
#include <stdbool.h>
#include <math.h>
int main( )
{
//    printf("Hello, World!\n");
    double quarter_pi = 0;
    double remainder = 0;
    bool flag = true;
    for(int i = 1; ; i += 2) {
        remainder = 1.0/i;
        if(remainder > pow(10, -6)) {
            if(flag) {
                quarter_pi += remainder;
                flag = false;
            } else {
                quarter_pi -= remainder;
                flag = true;
            }
        } else {
            break;
        }
        printf("i = %d, remainder = %lf, pi = %lf\n", i, remainder, quarter_pi*4);
    }

    return 0;
}

//i = 999975, remainder = 0.000001, pi = 3.141591
//i = 999977, remainder = 0.000001, pi = 3.141595
//i = 999979, remainder = 0.000001, pi = 3.141591
//i = 999981, remainder = 0.000001, pi = 3.141595
//i = 999983, remainder = 0.000001, pi = 3.141591
//i = 999985, remainder = 0.000001, pi = 3.141595
//i = 999987, remainder = 0.000001, pi = 3.141591
//i = 999989, remainder = 0.000001, pi = 3.141595
//i = 999991, remainder = 0.000001, pi = 3.141591
//i = 999993, remainder = 0.000001, pi = 3.141595
//i = 999995, remainder = 0.000001, pi = 3.141591
//i = 999997, remainder = 0.000001, pi = 3.141595
//i = 999999, remainder = 0.000001, pi = 3.141591
