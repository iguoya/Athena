#include "mainwindow.h"
#include "ui_mainwindow.h"
#include "Strategy/StrategyContext.h"
#include "Facade/Facade.h"
#include "Facade/Rocket.h"
#include "TemplateMethod/ConcreteClassA.h"
#include "TemplateMethod/ConcreteClassB.h"
#include "TemplateMethod/M1A1.h"
#include "TemplateMethod/T90.h"

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent)
    , ui(new Ui::MainWindow)
{
    ui->setupUi(this);
    render = new QSvgRenderer;

    ui->frame->autoFillBackground();
}

MainWindow::~MainWindow()
{
    delete ui;
}


void MainWindow::on_pushButton_clicked()
{
    ui->textEdit->clear();
    ui->frame->setStyleSheet("QFrame{border-image:url(:/UML/strategy.svg)}" );
    StrategyContext sc;

    for(auto &m: sc.run()) {
        ui->textEdit->append(QString::fromStdString(m));
    }
}


void MainWindow::on_pushButton_2_clicked()
{
    ui->textEdit->clear();
    ui->frame->setStyleSheet("QFrame{border-image:url(:/UML/facade.svg)}" );

    Facade fc;
    for(auto &m: fc.operation()) {
        ui->textEdit->append(QString::fromStdString(m));
    }
    Rocket rk;
    for(auto &m: rk.lanuch()) {
        ui->textEdit->append(QString::fromStdString(m));
    }
}


void MainWindow::on_pushButton_14_clicked()
{
    ui->textEdit->clear();
    ui->frame->setStyleSheet(
                "QFrame{border-image:url(:/UML/templatemethod.svg)}"
                );

    ConcreteClassA ca;
    ca.templateMethod();
    for(auto &m: ca.result) {
        ui->textEdit->append(QString::fromStdString(m));
    }
    ConcreteClassB cb;
    cb.templateMethod();
    for(auto &m: cb.result) {
        ui->textEdit->append(QString::fromStdString(m));
    }

    M1A1 m1;
    m1.attack();
    for(auto &m: m1.result) {
        ui->textEdit->append(QString::fromStdString(m));
    }
    T90 t90;
    t90.attack();
    for(auto &m: t90.result) {
        ui->textEdit->append(QString::fromStdString(m));
    }


}

