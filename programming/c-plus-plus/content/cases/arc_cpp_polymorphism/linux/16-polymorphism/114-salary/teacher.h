#ifndef TEACHER_H
#define TEACHER_H
#include "officer.h"

class teacher : public officer
{
public:
    teacher();
    void work();
    void salary();
};

#endif // TEACHER_H
