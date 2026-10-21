#include "mainwindow.h"
#include "ui_mainwindow.h"

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent)
    , ui(new Ui::MainWindow)
{
//    getHostInfomation();
    ui->setupUi(this);

}

MainWindow::~MainWindow()
{
    delete ui;
}

void MainWindow::getHostInformation()
{

//    QString localHostName = QHostInfo::localHostName();			//(a)
//    lineEditLocalHostName->setText(localHostName);
//    QHostInfo hostInfo = QHostInfo::fromName(localHostName);	//(b)
//    //获得主机的IP地址列表
//    QList<QHostAddress> listAddress = hostInfo.addresses();
//    if(!listAddress.isEmpty())									//(c)
//    {
//        lineEditAddress->setText(listAddress.at(2).toString());
//    }
}


void MainWindow::on_pushButtonDetail_clicked()
{
//    ui->lineEditLocalHostName = "sss";

}
