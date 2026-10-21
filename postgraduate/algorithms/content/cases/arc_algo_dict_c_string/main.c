#include <stdio.h>
#include <string.h>
#include <stdint.h>

int main() {
    int str_length = 10;
    char s1[str_length], s2[str_length];
    char t[str_length];

    //输入子串转数字
    printf("输入第一个字符串：\n");
    fgets(s1, str_length, stdin);
    printf("你输入的是：\n");
    fputs(s1, stdout);
    printf("转换后数字是：%d\n", atol(s1));
    fflush(stdin);
    printf("输入第二个字符串：\n");
    fgets(s2, str_length, stdin);
    printf("你输入的是：\n");
    fputs(s2, stdout);
    printf("转换后数字是：%d\n", atol(s2));

    strcpy(t, s1);
    strcpy(s1, s2);
    strcpy(s2, t);
    printf("交换之后：\n");

    printf("s1 :%s", s1);
    printf("s2 :%s", s2);

    printf("两个数字加和: %d\n", atol(s1)+atol(s2));


    char str[][11] = {"c language", "fox movies", "computer", "home page"};
//    char *t_str = {str[0], str[1], str[2], str[3]};

    printf("str[] size :%zu, str size :%zu\n", sizeof(*(str + 1)), sizeof(str));


    for(int i = 0; i < sizeof(str)/sizeof(*str); ++i) {
        printf("range:%d, size:%d, %d : %s\n",sizeof(str)/sizeof(*str), sizeof(str[i])/sizeof(char), i, str[i]);
    }

    char **p_str;
    p_str = str;

    printf("str addr :%p, p_str addr(%p) point addr : %p", str, &p_str, p_str);











    return 0;
}