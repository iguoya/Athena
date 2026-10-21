#include <iostream>
#include "Strategy.h"
#include "Context.h"
#include "ConcreteStrategyA.h"
#include "ConcreteStrategyB.h"

int main(int argc, char **argv)
{
    std::cout << "Hello World" << std::endl;
    Strategy *p_a = new ConcreteStrategyA();
    Strategy *p_b = new ConcreteStrategyB();
    
    Context *pc = new Context(p_a);
    pc->do_action();
    pc = new Context(p_b);
    pc->do_action();
    
    return 0;
}
