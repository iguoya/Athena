//
// Created by tiger on 18-11-9.
//

#include <stdio.h>

typedef  char StackElemType;
#include "stack.h"



bool symbol_matching(char *line, ssize_t len) {
    LinkStack top = init_stack();
    bool is_match = true;
    for (size_t i = 0; i <= len; ++i) {
        char symbol = line[i];
        if (symbol == '{' || symbol == '[' || symbol == '(') {
            push(top, symbol);
        } else {
            switch (symbol) {
                char left_symbol;
                case '}':
                    get_top(top, &left_symbol);
                    if (left_symbol == '{') {
                        pop(top);
                    } else {
                        is_match = false;
                    }
                    break;
                case ']':
                    get_top(top, &left_symbol);
                    if (left_symbol == '[') {
                        pop(top);
                    } else {
                        is_match = false;
                    }
                    break;
                case ')':
                    get_top(top, &left_symbol);
                    if (left_symbol == '(') {
                        pop(top);
                    } else {
                        is_match = false;
                    }
                    break;
            }
            if (is_match == false ) {
                break;
            }
        }

    }
    if(empty_stack(top) && is_match == true) {
        return true;
    } else {
        return false;
    }
}

int main() {
//    char c ;
//    while ((c = getchar()) != EOF) {
//        putchar(c);
//        printf("你输入的是：%c\n", c);
//
//    }
    char *line = NULL;
    size_t len = 0;
    ssize_t read;
    printf("请输入一个字符串：\n");
    while ((read = getline(&line, &len, stdin)) != -1) {
//        printf("Retrieved line of length %zu, %u :\n", read, len);
        printf("%s", line);
        if(symbol_matching(line, len)) {
            printf("匹配\n");
        } else {
            printf("不！匹配\n");
        }
    }
    return 0;
}