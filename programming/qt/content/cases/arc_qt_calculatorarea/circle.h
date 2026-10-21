#ifndef CIRCLE_H
#define CIRCLE_H

#include <QObject>

class Circle : public QObject
{
    Q_OBJECT

    Q_PROPERTY(QString area READ area WRITE setArea NOTIFY areaChanged)
public:
    explicit Circle(QObject *parent = nullptr);

    Q_INVOKABLE QString setArea(QString r);

    QString area();

    QString m_area;

signals:

    void areaChanged();

};

#endif // CIRCLE_H
