#include <iostream>
#include "AbstractClass.h"
#include "ConcreteClass1.h"
#include "ConcreteClass2.h"

int main(int argc, char **argv)
{
    std::cout << "Hello World" << std::endl;
     AbstractClass *s = new AbstractClass();
    AbstractClass *a = new ConcreteClass1();
    AbstractClass *b = new ConcreteClass2();
    s->TemplateMethod();
    
    a->TemplateMethod();
    b->TemplateMethod();
    return 0;
}
