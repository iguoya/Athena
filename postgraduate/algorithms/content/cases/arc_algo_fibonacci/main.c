#include <stdio.h>

int fibonacci(int n) {
    if(n <= 2) {
        return 1;
    }
    return fibonacci(n-1)+fibonacci(n-2);
}

int fibonacci_normal(int n) {
    int first_num = 1;
    int second_num = 1;
    if(n <= 2) return 1;
    int result = 0;
    for(int i = 3; i <= n; ++i) {
        result = first_num + second_num;
        first_num = second_num;
        second_num = result;
    }
    return result;
}

int main() {
    for(int i = 1; i<=40; ++i) {
        printf("%10d", fibonacci(i));
        if(i%5 == 0) {
            printf("\n");
        }
    }
    for(int i = 1; i<=40; ++i) {
        printf("%10d", fibonacci_normal(i));
        if(i%5 == 0) {
            printf("\n");
        }
    }
    return 0;
}
