#include <iostream>
using namespace std;

class Shape
{
protected:
    int width, height;

public:
    Shape(int a = 0, int b = 0)
    {
        width = a;
        height = b;
    }
    virtual void area()
    {
        cout << "Parent class area :" << endl;
    }
    virtual void say() = 0;
};
class Rectangle : public Shape
{
public:
    Rectangle(int a = 0, int b = 0) : Shape(a, b) {}
    void area()
    {
        cout << "Rectangle class area :" << (width * height)<<endl;
    }
    void say()
    {
        cout << "I am Rectangle" << endl;
    }
};
class Triangle : public Shape
{
public:
    Triangle(int a = 0, int b = 0) : Shape(a, b) {}
    void area()
    {
        cout << "Triangle class area :" << (width * height / 2) << endl;
    
    }
    void say()
    {
        cout << "I am Triangle" << endl;
    }
};
// 程序的主函数
int main()
{

    Shape *r = new Rectangle(10, 7);
    Shape *t = new Triangle(10, 5);
    r->say();
    r->area();

    // 调用三角形的求面积函数 area
    t->say();
    t->area();

    return 0;
}