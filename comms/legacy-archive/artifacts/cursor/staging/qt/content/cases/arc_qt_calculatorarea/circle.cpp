#include "circle.h"

Circle::Circle(QObject *parent) : QObject(parent)
{

}



void Circle::setArea(QString r)
{
    double m_r = r.toDouble();
    m_area = QString::number(3.14*m_r*m_r);
    emit areaChanged();
}

QString Circle::area()
{
    return m_area;
}

//void Circle::getArea(double r)
//{

//}
