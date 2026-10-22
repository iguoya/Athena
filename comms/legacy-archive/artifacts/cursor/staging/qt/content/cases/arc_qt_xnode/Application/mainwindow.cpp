#include "mainwindow.h"
#include "./ui_mainwindow.h"

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent)
    , ui(new Ui::MainWindow)
{
    ui->setupUi(this);
    connect(&process, &QProcess::readyRead, this, &MainWindow::readStatus);

//    hosts {
//        {"", , 8887, "A"},
//    };

//    ui->tableWidget->horizontalHeader()->setSectionResizeMode(QHeaderView::ResizeToContents);
//    ui->tableWidget->horizontalHeader()->setSectionResizeMode(QHeaderView::Stretch);//平均分配列宽
//    ui->treeWidget->horizontalHeader()->setSectionResizeMode(QHeaderView::Stretch);
}

MainWindow::~MainWindow()
{
    delete ui;
}


void MainWindow::on_pushButton_3_clicked()
{
//    const QString cmd();
//    const QStringList args;

    process.startDetached("/home/tiger/MultiNode/build-NodeServer-unknown-Debug/NodeServer",
                  {"127.0.0.1", "8887", "A"});

    process.startDetached("/home/tiger/MultiNode/build-NodeClient-unknown-Debug/NodeClient",
                  {"127.0.0.1", "8887", "B"});

    process.startDetached("/home/tiger/MultiNode/build-NodeClient-unknown-Debug/NodeClient",
                  {"127.0.0.1", "8887", "C"});

    process.startDetached("/home/tiger/MultiNode/build-NodeClient-unknown-Debug/NodeClient",
                  {"127.0.0.1", "8887", "D"});

//    const QStringList argsA{"-n"};
//    const QStringList argsB{"-l"};
//    process.start("route", argsA);
//    process.startDetached("ls", argsB);
//    process.startDetached("route", argsA);
}

void MainWindow::readStatus()
{
    ui->textBrowser->append(process.readAll());
}

