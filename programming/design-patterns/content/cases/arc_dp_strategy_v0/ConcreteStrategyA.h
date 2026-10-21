
#ifndef CONCRETESTRATEGYA_H
#define CONCRETESTRATEGYA_H
#include "Strategy.h"
#include <iostream>
#include <string>
using namespace std;
/**
  * class ConcreteStrategyA
  * 
  */

class ConcreteStrategyA : virtual public Strategy
{
public:

  // Constructors/Destructors
  //  


  /**
   * Empty Constructor
   */
  ConcreteStrategyA ();

  /**
   * Empty Destructor
   */
  virtual ~ConcreteStrategyA ();

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
  void new_operation ()
  {
      cout<<"方案A"<<endl;
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

#endif // CONCRETESTRATEGYA_H
