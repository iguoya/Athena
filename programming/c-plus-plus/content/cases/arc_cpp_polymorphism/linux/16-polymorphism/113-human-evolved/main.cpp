#include <iostream>
#include "animalancestor.h"
#include "ape.h"
#include "human.h"

using namespace std;

int main()
{
    cout << "Hello World!" << endl;
    AnimalAncestor animal;
    animal.respire();
    Ape ae;
    ae.respire();
    ae.move();
    Human man;
    man.respire();
    man.move();
    man.use_tools();
    return 0;
}
