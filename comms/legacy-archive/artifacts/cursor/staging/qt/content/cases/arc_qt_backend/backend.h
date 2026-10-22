#ifndef BACKEND_H
#define BACKEND_H

#include <QObject>

class  BackEnd : public QObject
{
    Q_OBJECT
    Q_PROPERTY(QString userName READ userName WRITE setUserName NOTIFY UserNameChanged)
public:
    explicit  BackEnd(QObject *parent = nullptr);
    void setUserName(QString userName);
    QString userName();
signals:
    void UserNameChanged();

private:
    QString m_userName;
};

#endif // BACKEND_H
