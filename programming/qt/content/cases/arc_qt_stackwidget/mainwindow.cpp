#include "mainwindow.h"
#include "ui_mainwindow.h"
#include "aframe.h"

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent)
    , ui(new Ui::MainWindow)
{
    ui->setupUi(this);
    AFrame *af = new AFrame;
    ui->stackedWidget->addWidget(af);

    connect(af, &AFrame::signalReturn, this, &MainWindow::returnMain);
}

MainWindow::~MainWindow()
{
    delete ui;
}

void MainWindow::returnMain()
{
    ui->stackedWidget->setCurrentIndex(0);
}


void MainWindow::on_pushButton_clicked()
{
    ui->stackedWidget->setCurrentIndex(1);
}
