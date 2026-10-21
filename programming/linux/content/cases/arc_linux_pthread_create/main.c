#include <stdio.h>
#include <pthread.h>
#include <unistd.h>

void print_thread_info(const char *s) {
    pid_t p_id = getpid();
    pthread_t t_id = pthread_self();
    printf("%s: pid: %d tid:%lu\n", s, p_id, t_id);
}

void *thread_new_run(void *arg) {
    print_thread_info(arg);
    return NULL;
}

int main()
{
    printf("Hello World!\n");
    pthread_t new_tid;
    pthread_create(&new_tid, NULL, thread_new_run, "我是新线程");
    printf("新线程id: "
"%lu\n", new_tid);
    print_thread_info("我是父进程");
    sleep(2);
    return 0;
}
