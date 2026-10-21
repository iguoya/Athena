#include <stdio.h>
#include <pthread.h>
#include <stdlib.h>
#include <unistd.h>

typedef struct Student {
    int qq;
    char name[100];
} Student;

void *thread_one(void *arg) {
    printf("\nthread 1 running !!!\n");
    for(int i = 1; i <= 10; ++i) {
        printf("%d\t", i);
        if(i % 10 == 0) {
            printf("\n");
        }
        sleep(1);
    }
    return "hello";
}

void *thread_two(void *arg) {
    printf("\nthread 2 running !!!\n");
    for(int i = 101; i <= 110; ++i) {

        printf("%d\t", i);
        if(i % 10 == 0) {
            printf("\n");
        }
        sleep(2);
    }


    Student *s = malloc(sizeof(Student));
    s->qq = 150657100;
    snprintf(s->name, sizeof(s->name), "%s", "郭雅");
//    s.name = ""

    return s;
}

int main()
{
    printf("Hello World!\n");

    pthread_t tid = 0, tid2 = 0;
    void *result = NULL;
    pthread_create(&tid, NULL, thread_one, NULL);



    pthread_create(&tid2, NULL, thread_two, NULL);

    pthread_join(tid2, &result);
    pthread_join(tid, &result);

    printf("\nthread 1 exit code: %s\n", (char *)result);
    Student *s = (Student *)result;//返回结构体指针
    printf("\nthread 2 exit code: qq :%d, name :%s\n", s->qq, s->name);
    return 0;
}
