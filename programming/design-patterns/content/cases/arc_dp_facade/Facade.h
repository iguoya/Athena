#ifndef FACADE_H
#define FACADE_H
#include <string>
#include <vector>
#include "SubSystemA.h"
#include "SubSystemB.h"
using namespace std;

class Facade {

private:
//	SubSystemB subSystemB;
//	SubSystemA subSystemA;
	SubSystemA* subA;
	SubSystemB* subB;

public:
    vector<string> operation();

	Facade();
};

#endif
