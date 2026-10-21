
#ifndef ADAPTER_H
#define ADAPTER_H
#include "Target.h"

#include <string>

/**
  * class Adapter
  * 
  */

class Adapter : virtual public Target
{
public:

    // Constructors/Destructors
    //  


    /**
     * Empty Constructor
     */
    Adapter ();

    /**
     * Empty Destructor
     */
    virtual ~Adapter ();

    // Static Public attributes
    //  

    // Public attributes
    //  


    // Public attribute accessor methods
    //  


    // Public attribute accessor methods
    //  



    /**
     */
    void request ()
    {
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

    Adaptee * adaptee;
public:


    // Private attribute accessor methods
    //  

private:

public:


    // Private attribute accessor methods
    //  


    /**
     * Set the value of adaptee
     * @param new_var the new value of adaptee
     */
    void setAdaptee (Adaptee * new_var)     {
            adaptee = new_var;
    }

    /**
     * Get the value of adaptee
     * @return the value of adaptee
     */
    Adaptee * getAdaptee ()     {
        return adaptee;
    }
private:


    void initAttributes () ;

};

#endif // ADAPTER_H
