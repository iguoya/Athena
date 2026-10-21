#include <stdio.h>

struct date {
    short year;
    short month;
    short day;
};

struct student {
    char name[20];
    int score;
    struct date birthday;
};

int main() {
    printf("Hello, World! %s(%d)\n", "皇甫珍竹", sizeof("皇甫珍竹"));

    struct student g1c1[] = {
            {"皇甫珍竹", 88, 1988, 6, 13},
            {"尤宜萍",  88, 1989, 8, 12},
    };
    struct student *p;
    p = g1c1;

    int length = sizeof(g1c1) / sizeof(g1c1[0]);
//    printf("size:%d, %d", sizeof(g1c1), sizeof(g1c1[0]));
    for (int i = 0; i < length; ++i) {
        printf("%s(%d), %d, %d, %d, %d\n",
               g1c1[i].name,
               sizeof(g1c1[i].name),
               g1c1[i].score,
               g1c1[i].birthday.year,
               g1c1[i].birthday.month,
               g1c1[i].birthday.day);
        printf("%s(%d), %d, %d, %d, %d\n",
               p->name,
               sizeof(p->name),
               p->score,
               p->birthday.year,
               p->birthday.month,
               p->birthday.day);
        ++p;
    }

    return 0;
}