
#ifndef CONCRETECLASS1_H
#define CONCRETECLASS1_H
#include "AbstractClass.h"
#include <iostream>
#include <string>
using namespace std;

/**
  * class ConcreteClass1
  * 
  */

class ConcreteClass1 : virtual public AbstractClass
{
public:

  // Constructors/Destructors
  //  


  /**
   * Empty Constructor
   */
  ConcreteClass1 ();

  /**
   * Empty Destructor
   */
  virtual ~ConcreteClass1 ();

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
      cout<<"子类1自定义操作A"<<endl;
  }


  /**
   */
  void new_operation_1 ()
  {
      cout<<"子类1自定义操作B"<<endl;
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

#endif // CONCRETECLASS1_H
