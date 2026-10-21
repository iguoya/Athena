#include <iostream>


#include "teacher.h"
#include "doctor.h"

using namespace std;

int main()
{
    cout << "Hello World!" << endl;
    officer *t = new teacher();
    t->work();
    t->salary();


    officer *d = new doctor();
    d->work();
    d->salary();

    return 0;
}
