//
// Created by tiger on 18-11-12.
//

#include <stdio.h>

typedef char* QueueElemType;
#include "queue.h"
void show_queue(LinkQueue lq) {
    LinkQueueNode ln = lq->front;
    while(ln != lq->rear) {
        printf("%s\n", ln->next->data);
        ln = ln->next;
    }
}


int main() {
//    printf("Hello, World!\n");
    LinkQueue male = init_queue();
    en_queue(male, "张三");
    en_queue(male, "李四");
    en_queue(male, "王五");
    en_queue(male, "赵六");
    show_queue(male);

    LinkQueue female = init_queue();
    en_queue(female, "小桃");
    en_queue(female, "小红");
    en_queue(female, "小璐");
    show_queue(female);
    int i = 1;
    while(i<20) {
        char *boy = malloc(sizeof(100));
        char *girl = malloc(sizeof(100));
        if(get_queue_head(male, &boy) && get_queue_head(female, &girl)) {
            printf("%s和%s跳舞\n", boy, girl);
            de_queue(male);
            de_queue(female);
            en_queue(male, boy);
            en_queue(female, girl);
        }
        ++i;
    }
    return 0;
}