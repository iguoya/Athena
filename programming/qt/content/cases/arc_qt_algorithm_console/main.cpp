#include "mainwindow.h"

#include <QApplication>
#include <QFile>
#include <QTextStream>

int main(int argc, char *argv[])
{
    QApplication a(argc, argv);

    QFile file(":/qdarkstyle/dark/darkstyle.qss");
    file.open(QIODevice::ReadOnly);
    QTextStream in(&file);
    qApp->setStyleSheet(in.readAll());

    MainWindow w;
    w.showMaximized();
    return a.exec();
}
