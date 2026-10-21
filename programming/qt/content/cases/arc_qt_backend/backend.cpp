#include "backend.h"

 BackEnd:: BackEnd(QObject *parent) : QObject(parent)
{

}

void  BackEnd::setUserName(QString userName)
{
    this->m_userName = userName;
    emit UserNameChanged();
}

QString BackEnd::userName()
{
    return m_userName;
}
