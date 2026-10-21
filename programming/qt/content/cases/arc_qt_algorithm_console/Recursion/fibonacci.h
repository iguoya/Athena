#ifndef FIBONACCI_H
#define FIBONACCI_H

#include <QObject>

class Fibonacci : public QObject
{
    Q_OBJECT
public:
    explicit Fibonacci(QObject *parent = nullptr);

signals:

};

#endif // FIBONACCI_H
