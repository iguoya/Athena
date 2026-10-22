#include <QCoreApplication>
#include <QProcess>
#include <QDebug>

int main(int argc, char *argv[])
{
    QCoreApplication a(argc, argv);

    QProcess process;
    process.start("ps -ax -ocmd ");
    QByteArray result;
    if(process.waitForFinished())
    {
        result = process.readAllStandardOutput();

    }
    auto s = result.split('\n');
//    qDebug()<<s;

    auto i = s.begin();
    while(i != s.end()) {
        qDebug()<<*i;   
        qDebug()<<"--------------\n";
        ++i;
    }


//    foreach result
    return a.exec();
}
