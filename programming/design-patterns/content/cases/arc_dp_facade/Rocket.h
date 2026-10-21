#ifndef ROCKET_H
#define ROCKET_H
#include <vector>
#include <string>
#include "Navigation.h"
#include "Power.h"

using namespace std;
class Rocket {

private:
	Navigation navigation;
    Power power;
    vector<string> result;
//	Navigation navigator;

public:
    vector<string> lanuch();
};

#endif
