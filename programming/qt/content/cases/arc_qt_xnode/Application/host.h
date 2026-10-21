#ifndef HOST_H
#define HOST_H

#include <QObject>
class Host
{
public:
    Host(QString app, QString ip, ushort port, QString name):
        app(app), ip(ip), port(port), name(name){};

    QString app;
    QString ip;
    ushort port;
    QString name;
};

#endif // HOST_H
