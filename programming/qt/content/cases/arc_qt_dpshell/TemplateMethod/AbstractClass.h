/**
 * Project StartUML_DP
 */


#ifndef _ABSTRACTCLASS_H
#define _ABSTRACTCLASS_H
#include <vector>
#include <string>
using namespace std;

class AbstractClass {
public: 
    vector<string> result;
    
    virtual string Operation1() = 0;
    
    virtual string Operation2() = 0;
    
    virtual string Operation3() = 0;
    
    void templateMethod(){
        result.push_back(Operation1());
        result.push_back(Operation2());
        result.push_back(Operation3());
    };
};

#endif //_ABSTRACTCLASS_H
