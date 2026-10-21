
#ifndef CONCRETECLASS2_H
#define CONCRETECLASS2_H
#include "AbstractClass.h"

#include <string>

/**
  * class ConcreteClass2
  * 
  */

class ConcreteClass2 : virtual public AbstractClass
{
public:

  // Constructors/Destructors
  //  


  /**
   * Empty Constructor
   */
  ConcreteClass2 ();

  /**
   * Empty Destructor
   */
  virtual ~ConcreteClass2 ();

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
      cout<<"子类2仅仅自定义了操作A,操作B使用默认"<<endl;
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

#endif // CONCRETECLASS2_H
