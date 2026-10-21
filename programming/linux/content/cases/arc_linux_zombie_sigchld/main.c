#include <stdio.h>
#include <unistd.h>
#include <signal.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <stdlib.h>

void signal_terminated();

int main()
{
    printf("Hello World!\n");

    pid_t p_id = fork();
    if(p_id < 0) {
        perror("fork error");
        exit(1);
    }

    if(p_id > 0) {
        for(int i = 0; i < 10; ++i) {
            sleep(2);
            signal(SIGCHLD, signal_terminated);//Child terminated or stopped.
            printf("I am Parent, No: %d\n", i);
        }
    } else {
        for(int i = 0; i < 5; ++i) {
            sleep(2);
            printf("I am Child: No %d\n", i);
        }
        exit(2);
    }
    return 0;
}


void signal_terminated(int signal) {
    pid_t p = 0;
    int i = 0;
    waitpid(p, &i, 0);
    printf("num: %d\n", WEXITSTATUS(i));
}
