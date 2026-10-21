
#ifndef FACTORY_H
#define FACTORY_H
#include <iostream>
#include <string>
using namespace std;
#include "ConcreteProductA.h";
#include "ConcreteProductB.h";
#include "ConcreteProductC.h";
/**
  * class Factory
  *
  */

class Factory
{
public:

    // Constructors/Destructors
    //


    /**
     * Empty Constructor
     */
    Factory ();

    /**
     * Empty Destructor
     */
    virtual ~Factory ();

    // Static Public attributes
    //

    // Public attributes
    //


    // Public attribute accessor methods
    //


    // Public attribute accessor methods
    //



    /**
     * @return Product *
     * @param  name
     */
    Product * CreateProduct (string name)
    {
        if(name == "A") {
                cout<<"创造产品A"<<endl;
            return new ConcreteProductA();
        }

        if(name == "B") {
                cout<<"创造产品B"<<endl;
            return new ConcreteProductB();
        }

        if(name == "C") {
                cout<<"创造产品C"<<endl;
            return new ConcreteProductC();
        }
    }

protected:

    // Static Protected attributes
    //

    // Protected attributes
    //

public:


    // Protected attribute accessor methods
    //

protected:

public:


    // Protected attribute accessor methods
    //

protected:


private:

    // Static Private attributes
    //

    // Private attributes
    //

public:


    // Private attribute accessor methods
    //

private:

public:


    // Private attribute accessor methods
    //

private:



};

#endif // FACTORY_H
