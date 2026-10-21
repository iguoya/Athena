#include <iostream>
 
int count ;
extern void write_extern();
 
int main()
{
   count = 5;
   write_extern();
   std::cout << "end: count  :" << count << std::endl;
}