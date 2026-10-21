#include <stdio.h>
#include <stdbool.h>
#include <math.h>
#include <stdint.h>

bool is_prime(long int n) {
    for(long int i = 2; i <= sqrt(n); ++i) {
        if(n % i == 0) {
            return false;
        } else {
            continue;
        }
    }
    return true;
}
long int get_next_prime(long int n) {
    n = n + 1;
    while(true) {
        if(is_prime(n)) {
            break;
        } else {
            ++n;
        }
    }
    return n;
}

int main() {
    printf("int size :%d, long size: %d, long int size :%d\n", sizeof(int), sizeof(long int), sizeof(intmax_t));
//    printf("max int :%d, max long int :%ld\n", powl(2, 3), powl(2, 8*4));
    while(true) {
        long int number;
        printf("任意输入一个偶数:\n");
        scanf("%jd", &number);
        printf("你输入的是:%jd\n", number);
        long int first_prime = 2;
        while(true) {

            long int second_prime = number - first_prime;

            if(is_prime(second_prime)) {
                printf("ok!!!, get %ld = %ld + %ld\n", number, first_prime, second_prime);
                break;
            } else {
                first_prime = get_next_prime(first_prime);
                second_prime = number - first_prime;
                printf("test:%ld, %ld\n", first_prime, second_prime);
            }
        }
    }


    return 0;
}
//int size :4, long size: 8, long int size :8
//任意输入一个偶数:
//888888888888
//你输入的是:888888888888
//test:3, 888888888885
//test:5, 888888888883
//test:7, 888888888881
//test:11, 888888888877
//test:13, 888888888875
//test:17, 888888888871
//test:19, 888888888869
//test:23, 888888888865
//test:29, 888888888859
//ok!!!, get 888888888888 = 29 + 888888888859
//任意输入一个偶数:
//100000000000
//你输入的是:100000000000
//test:3, 99999999997
//test:5, 99999999995
//test:7, 99999999993
//test:11, 99999999989
//test:13, 99999999987
//test:17, 99999999983
//test:19, 99999999981
//test:23, 99999999977
//ok!!!, get 100000000000 = 23 + 99999999977
//任意输入一个偶数:
