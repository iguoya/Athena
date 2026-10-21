#include <iostream>
 
extern int count;
 
void write_extern(void)
{
   std::cout << "begin: count  :" << count << std::endl;
   count = 100;
   std::cout << "count  changed " << std::endl;
}
