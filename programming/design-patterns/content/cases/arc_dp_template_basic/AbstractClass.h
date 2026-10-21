
#ifndef ABSTRACTCLASS_H
#define ABSTRACTCLASS_H
#include <iostream>
#include <string>
using namespace std;

/**
  * class AbstractClass
  * 
  */

class AbstractClass
{
public:


  // Public attribute accessor methods
  //  


  // Public attribute accessor methods
  //  



  /**
   */
  virtual void TemplateMethod ()
  {
      new_operation();
      new_operation_1();
  }

protected:

public:


  // Protected attribute accessor methods
  //  

protected:

public:


  // Protected attribute accessor methods
  //  

protected:



  /**
   */
  virtual void new_operation ()
  {
      cout<<"默认操作A"<<endl;
  }


  /**
   */
  virtual void new_operation_1 ()
  {
      cout<<"默认操作B"<<endl;
  }

private:

public:


  // Private attribute accessor methods
  //  

private:

public:


  // Private attribute accessor methods
  //  

private:



};

#endif // ABSTRACTCLASS_H
