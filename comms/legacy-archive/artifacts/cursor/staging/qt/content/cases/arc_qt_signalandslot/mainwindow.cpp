#include "mainwindow.h"
#include "ui_mainwindow.h"
//#include "hello.h"
#include "tiger.h"

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent)
    , ui(new Ui::MainWindow)
{
    ui->setupUi(this);
//    Hello *h = new Hello();
//    Tiger *t = new Tiger();
//    connect(ui->pushButton, &QPushButton::clicked, h, &Hello::say);
     connect(ui->pushButton, &QPushButton::clicked, new Tiger(), &Tiger::testHello);
//     connect
}

MainWindow::~MainWindow()
{
    delete ui;
}

