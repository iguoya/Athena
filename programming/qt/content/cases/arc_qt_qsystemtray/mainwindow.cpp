#include "mainwindow.h"
#include "ui_mainwindow.h"

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent)
    , ui(new Ui::MainWindow)
{
    ui->setupUi(this);
    QSystemTrayIcon *trayIcon= new QSystemTrayIcon(this);
    trayIcon->setIcon(QIcon(":/soft.ico"));
    connect(trayIcon,SIGNAL(activated(QSystemTrayIcon::ActivationReason)),
            this,SLOT(iconActivated(QSystemTrayIcon::ActivationReason)));
    trayIcon->show();


}

MainWindow::~MainWindow()
{
    delete ui;
}
void MainWindow::iconActivated(QSystemTrayIcon::ActivationReason reason)

{
    switch(reason)
    {
    case QSystemTrayIcon::Trigger :
        setWindowState(Qt::WindowActive);
        activateWindow();
        break;
    default:
        break;
    }
}

