#include "define.h"

Define::Define()
{

}

void Define::run()
{

    std::cout << "Value of __LINE__ : " << __LINE__ << std::endl;
    std::cout << "Value of __FILE__ : " << __FILE__ << std::endl;
    std::cout << "Value of __DATE__ : " << __DATE__ << std::endl;
    std::cout << "Value of __TIME__ : " << __TIME__ << std::endl;
}
