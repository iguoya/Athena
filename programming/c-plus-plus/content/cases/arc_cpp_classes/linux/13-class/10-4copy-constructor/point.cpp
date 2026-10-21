#include "point.h"
#include <iostream>
using namespace std;

int Point::Sum = 0;

Point::Point()
{


}

Point::Point(int m, int n):x(m), y(n)
{
    ++Sum;

}

Point::Point(const Point & p)
{
    x = p.x + 10000;
    y = p.y + 10000;
    ++Sum;
}

void Point::add_point(Point &p)
{
    x += p.x;
    y += p.y;
}

void Point::show()
{
    cout<<"总共"<<Sum<<"个对象"<<endl;
    cout<<"Point("<<x<<","<<y<<")"<<endl;
}



Point Point::generate_point()
{
    return Point(666, 999);
}


