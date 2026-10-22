/**
 * Project StartUML_DP
 */


#ifndef _TANK_H
#define _TANK_H
#include <vector>
#include <string>
using namespace std;

class Tank {
public: 
    vector<string> result;
    virtual string reload() = 0;
    
    virtual string aiming() = 0;
    
    virtual string fire() = 0;
    
    void attack(){
        result.push_back(reload());
        result.push_back(aiming());
        result.push_back(fire());
    };
};

#endif //_TANK_H
