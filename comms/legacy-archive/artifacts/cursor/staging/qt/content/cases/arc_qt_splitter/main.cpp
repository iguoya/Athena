#include "mainwindow.h"

#include <QApplication>
#include <QSplitter>
#include <QTextEdit>

int main(int argc, char *argv[])
{
    QApplication a(argc, argv);
    QFont font("ZYSong18030", 16);
    a.setFont(font);
    QSplitter *splitterMain = new QSplitter(Qt::Horizontal, 0);
    QTextEdit *textLeft = new QTextEdit(QObject::tr("左边区域"), splitterMain);
    textLeft->setAlignment(Qt::AlignCenter);

    QSplitter *splitterRight = new QSplitter(Qt::Vertical, splitterMain);
    splitterRight->setOpaqueResize(false);
    QTextEdit *textUp = new QTextEdit(QObject::tr("上半部分"), splitterRight);
    textUp->setAlignment(Qt::AlignCenter);

    QTextEdit *textBotton = new QTextEdit(QObject::tr("下半部分"), splitterRight);
    textBotton->setAlignment(Qt::AlignCenter);

    splitterMain->setStretchFactor(1,1);
    splitterMain->setWindowTitle(QObject::tr("分割"));
    splitterMain->show();






//    MainWindow w;
//    w.show();
    return a.exec();
}
