#include <stdio.h>
#include <unistd.h>
#include <pthread.h>

int counter = 0;

void *run(void *arg) {
//    int *m = (int *)arg;
//    printf("Hello, %d\n", arg);
    int *seconds = (int *)arg;
    for(int i = 0; i< 10; ++i) {
        int val = counter;
        sleep(*seconds);
        printf("%x: %d\n", (unsigned int)pthread_self(), counter);
        counter = val+1;
    }
    return NULL;
}

int main()
{
    printf("Hello World!\n");

    pthread_t t_id, t_id2;
    pthread_create(&t_id, NULL, run, (void *)1) ;
    pthread_create(&t_id2, NULL, run, (void *)2);
    pthread_join(t_id, NULL);
    pthread_join(t_id2, NULL);

    return 0;
}
