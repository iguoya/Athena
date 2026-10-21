//
// Created by tiger on 18-12-6.
//

#include <stdio.h>
#include <stdlib.h>

void dec_to_bin(int n) {
    if(n == 0) {
        printf("\n算出二进制结果:\n");
    } else {
        dec_to_bin(n/2);
        printf("%d", n%2);
    }
}

int number_representation(int number, int base, int *result) {
    static int index = 0;
    if(number >= base) {
        result[index] = number % base;
        ++index;
        number = number / base;
        if(number != 0) {
            return number_representation(number, base, result);
        }
    } else {
        result[index] = number;
        int result_index = index;
        index = 0;
        return result_index;
    }
}

int main() {
    // 进制转换
//        dec_to_bin(10);
//        dec_to_bin(128);
//        dec_to_bin(256);
//        dec_to_bin(512);
//        dec_to_bin(1023);
    int result[20] = {0};
    int index = number_representation(127, 2, result);
    int result2[20] = {0};
    int index2 = number_representation(10, 3, result2);
    int result3[20] = {0};
    int index3 = number_representation(512, 8, result3);
    printf("%d, %d, %d\n", index, index2, index3);
}



