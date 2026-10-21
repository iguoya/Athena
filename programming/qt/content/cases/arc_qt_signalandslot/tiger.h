#ifndef TIGER_H
#define TIGER_H

#include <QObject>

class Tiger: public QObject
{
    Q_OBJECT
public:
    explicit Tiger(QObject *parent = nullptr);

public slots:
    void work();
    void testHello();
};

#endif // TIGER_H
