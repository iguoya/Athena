#ifndef DOCTOR_H
#define DOCTOR_H
#include "officer.h"

class doctor : public officer
{
public:
    doctor();
    void work();
    void salary();
};

#endif // DOCTOR_H
