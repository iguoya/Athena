
#ifndef CONCRETESTRATEGYB_H
#define CONCRETESTRATEGYB_H
#include "Strategy.h"
#include <iostream>
#include <string>
using namespace std;

/**
  * class ConcreteStrategyB
  * 
  */

class ConcreteStrategyB : virtual public Strategy
{
public:

  // Constructors/Destructors
  //  


  /**
   * Empty Constructor
   */
  ConcreteStrategyB ();

  /**
   * Empty Destructor
   */
  virtual ~ConcreteStrategyB ();

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
      cout<<"方案B"<<endl;
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

#endif // CONCRETESTRATEGYB_H
