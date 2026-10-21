#include <stdio.h>
typedef int QueueElemType;
#include "queue.h"

int main() {
//    printf("Hello, World!\n");
//    int two_dimensional[3][3];
//    int one_dimensional[9];
//    printf("two_demensional\n");
//
//    int *p = (int *)two_dimensional;//!!!!!强制转换
//
//    for(int i = 0; i < 3; ++i) {
//        for(int j = 0; j<3; ++j) {
//            printf("%p\t", &two_dimensional[i][j]);
//        }
//    }
//    printf("\n");
//    for(int i = 0; i < 3; ++i) {
//        for(int j = 0; j<3; ++j) {
//            printf("%p\t", two_dimensional[i]+j);
//        }
//    }
//    printf("\n");
//    for(int i = 0; i < 3; ++i) {
//        for(int j = 0; j<3; ++j) {
//            printf("%p\t", p+i*3+j);
//        }
//    }
//
//    printf("\none_demensional\n");
//    for(int i = 0; i < 9; ++i) {
//        printf("%p\t", &one_dimensional[i]);
//    }

    //杨辉三角

    int range = 15;
//    printf("输入层数:\n");
//    size_t blank_max = 15;
//    scanf("%d", &range);
    LinkQueue last_level = init_queue();
//    en_queue(last_level, 1);
    LinkQueue current_level = init_queue();

    for(int level = 1; level <= range; ++level) {

        for(int i = range-level; i > 0; --i) {
            printf("%3c", ' ');
        }


        for(int index = 1; index <= level; ++index) {
            if(index == 1) {
                en_queue(current_level, 1);
                if(index == level) {
                    //处理 第一层节点
                    int value = 0;
                    get_queue_head(current_level, &value);

                    printf("%3d\n", value);
                    de_queue(current_level);
                }
            } else {
                if(index == level) {
                    de_queue(last_level);
//                    if(empty_queue(last_level)) {
//                        printf("correct !! last_level empty\n");
//                    }
                    en_queue(current_level, 1);
                    //show current level

                    while(!empty_queue(current_level)) {
                        int value = 0;
                        get_queue_head(current_level, &value);
                        printf("%3d", value);
                        printf("%3c", ' ');
                        de_queue(current_level);
                        en_queue(last_level, value);
                    }
                    printf("\n");
                } else {
                    int first_num, second_num;
                    get_queue_head(last_level, &first_num);
                    de_queue(last_level);
                    get_queue_head(last_level, &second_num);
                    en_queue(current_level, first_num+second_num);
                }
            }
        }
    }

    return 0;
}

