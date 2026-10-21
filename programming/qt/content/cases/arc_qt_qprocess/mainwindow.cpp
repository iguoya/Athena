#include "mainwindow.h"
#include "ui_mainwindow.h"
#include <QProcess>
#include <QDebug>
MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent)
    , ui(new Ui::MainWindow)
{
    ui->setupUi(this);
}

MainWindow::~MainWindow()
{
    delete ui;
}


void MainWindow::on_pushButton_clicked()
{
    QStringList  argument;
    argument<< "-t" << "-s" << "3600";
    QStringList qstrList;
    qstrList<<"Android" << "Qt Creator" << "Java" << "C++";
    QStringListIterator strIterator(qstrList);
    while (strIterator.hasNext())
          qDebug() << strIterator.next();

    QProcess::startDetached("shutdown", argument);
}

void MainWindow::on_pushButton_2_clicked()
{
    QStringList  argument;
    argument<<"-i" << "cheese" ;
    QStringListIterator strIterator(argument);
    while (strIterator.hasNext())
          qDebug() << strIterator.next();

    QProcess::startDetached("killall", argument);

}

void MainWindow::on_pushButton_3_clicked()
{
//    QStringList  argument;
//    argument<<"-i" << "gedit" ;
    QStringList qstrList;
    qstrList<<"Android" << "Qt Creator" << "Java" << "C++";
    QProcess tigerProcess;
    tigerProcess.start("cheese", qstrList, 0);
}
