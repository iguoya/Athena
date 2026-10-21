#include "Context.h"

// Constructors/Destructors
//  

Context::Context () {
initAttributes();
}

Context::~Context () {
    if(!_stg) {
        delete _stg;
    }
 }

//  
// Methods
//  
Context::Context (Strategy * stg)
  {
      _stg = stg;
  }

  void Context::do_action()
  {
      _stg->new_operation();
  }
// Accessor methods
//  


// Other methods
//  

void Context::initAttributes () {

}

