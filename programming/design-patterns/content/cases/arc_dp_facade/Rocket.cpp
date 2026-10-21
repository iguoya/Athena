#include "Rocket.h"

vector<string> Rocket::lanuch() {
	// TODO - implement Rocket::lanuch
//	throw "Not yet implemented";
    result.push_back(power.run());
    result.push_back(navigation.run());
    return result;
}
