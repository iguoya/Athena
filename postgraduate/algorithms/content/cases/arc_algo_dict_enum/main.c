#include <stdio.h>
#include <stdlib.h>

int main() {
    printf("判断n能否被3,5,7整除\n");
    while (1) {

        printf("输入数字n:\n");
        int n;
        scanf("%d", &n);
        char result[3];
        result[2] = (n % 3 == 0 ? '1' : '0');
        result[1] = (n % 5 == 0 ? '1' : '0');
        result[0] = (n % 7 == 0 ? '1' : '0');
        printf("%s:%d\n", result, atoi(result));

        switch (atoi(result)) {
            case 0://case '000':
                printf("不被3,5,7整除\n");
                break;
            case 1://case '001':
                printf("被3整除\n");
                break;
            case 10://case '010':
                printf("被5整除\n");
                break;
            case 11://case '011':
                printf("被3,5整除\n");
                break;
            case 100://case '100':
                printf("被7整除\n");
                break;
            case 101://case '101':
                printf("被3,7整除\n");
                break;
            case 110://case '110':
                printf("被5,7整除\n");
                break;
            case 111://case '111':
                printf("被3,5,7整除\n");
                break;
        }

    }

    return 0;
}