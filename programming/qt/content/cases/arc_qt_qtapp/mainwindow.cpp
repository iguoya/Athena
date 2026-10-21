#include "mainwindow.h"
#include "./ui_mainwindow.h"
#include <QFontDatabase>

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent)
    , ui(new Ui::MainWindow)
{
    ui->setupUi(this);

    ui->toolBar->addAction(ui->action_system);
    ui->toolBar->addSeparator();
    ui->toolBar->addAction(ui->action_thread);
    ui->toolBar->addSeparator();
    ui->toolBar->addAction(ui->action_thread);
    ui->toolBar->addSeparator();
    ui->toolBar->addAction(ui->action_process);
    ui->toolBar->addSeparator();
    ui->toolBar->addAction(ui->action_ipc);
    ui->toolBar->addSeparator();
    ui->toolBar->addAction(ui->action_driver);
    ui->toolBar->addSeparator();
    ui->toolBar->addAction(ui->action_kernel);
    ui->toolBar->addSeparator();
    ui->toolBar->addAction(ui->action_exit);
    ui->toolBar->addSeparator();

    ui->MainLayout->addWidget(&system);
    currentWindow = &system;
    //    ui->LeftLayout->addWidget(&system);
    //    ui->RightLayout->addWidget(&table_view);

    //    leftWidget = &system;
    //    rightWidget = &table_view;
    //    item_model->setHorizontalHeaderLabels(column);
    //    connect(&system, &System::setLabels, table_view.model, &QStandardItemModel::setHorizontalHeaderLabels);
    //    connect(&system, &System::setData, &table_view, &TableView::setData);

    //    connect(&thread, &Thread::setModel, &multi_task, &MultiTask::setModel);
    //    ui->System->setIcon(QIcon(":/images/systemcall.svg"));
    //    ui->System->setIconSize(QSize(128,128));
    //    ui->Thread->setIcon(QIcon(":/images/thread.svg"));
    //    ui->Process->setIcon(QIcon(":/images/process.svg"));
    //    ui->Network->setIcon(QIcon(":/images/network.svg"));
    //    ui->IPC->setIcon(QIcon(":/images/ipc.svg"));
    //    ui->Driver->setIcon(QIcon(":/images/driver.svg"));
    //    ui->Kernel->setIcon(QIcon(":/images/kernel.svg"));
    //      ui->System->setIcon(QIcon(":/images/systemcall.svg"));
    //       ui->System->setIcon(QIcon(":/images/systemcall.svg"));


}

MainWindow::~MainWindow()
{
    delete ui;
}



void MainWindow::on_action_system_triggered()
{
    if(currentWindow != &system) {
        currentWindow->hide();
        ui->MainLayout->replaceWidget(currentWindow, &system);
        currentWindow = &system;
        currentWindow->show();
    }
}

void MainWindow::on_action_thread_triggered()
{
    if(currentWindow != &thread) {
        currentWindow->hide();
        ui->MainLayout->replaceWidget(currentWindow, &thread);
        currentWindow = &thread;
        currentWindow->show();
    }

}

void MainWindow::on_action_process_triggered()
{

}
