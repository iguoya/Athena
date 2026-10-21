#ifndef POINT_H
#define POINT_H


class Point
{
public:
    int x, y;

public:
    Point();
    Point(int m, int n);

    Point(const Point & p);

    void add_point(Point &p);

    void show();


    static Point generate_point();
    static int Sum;

};



#endif // POINT_H
