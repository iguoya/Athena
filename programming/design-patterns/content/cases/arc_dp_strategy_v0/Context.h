
#ifndef CONTEXT_H
#define CONTEXT_H
#include "Strategy.h"
#include <string>
#include <vector>



/**
  * class Context
  * 
  */

class Context
{
public:

  // Constructors/Destructors
  //  


  /**
   * Empty Constructor
   */
  Context ();

  /**
   * Empty Destructor
   */
virtual ~Context ();

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
  void do_action();


  /**
   * @param  stg
   */
   Context (Strategy * stg);

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

  Strategy * _stg;
public:


  // Private attribute accessor methods
  //  

private:

public:


  // Private attribute accessor methods
  //  


  /**
   * Set the value of _stg
   * @param new_var the new value of _stg
   */
  void set_stg (Strategy * new_var)   {
      _stg = new_var;
  }

  /**
   * Get the value of _stg
   * @return the value of _stg
   */
  Strategy * get_stg ()   {
    return _stg;
  }
private:


  void initAttributes () ;

};

#endif // CONTEXT_H
