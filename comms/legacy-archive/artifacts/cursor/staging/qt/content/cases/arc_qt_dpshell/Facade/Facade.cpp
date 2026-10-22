#include "Facade.h"

vector<string> Facade::operation() {
	// TODO - implement Facade::operation
//	throw "Not yet implemented";
    vector<string> result;
    result.push_back(subA->operation());
    result.push_back(subB->operation());
    return result;
}

Facade::Facade() {
	// TODO - implement Facade::Facade
//	throw "Not yet implemented";
    subA = new SubSystemA;
    subB = new SubSystemB;
}
