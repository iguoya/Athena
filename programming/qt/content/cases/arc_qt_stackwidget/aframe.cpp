#include "aframe.h"
#include "ui_aframe.h"

AFrame::AFrame(QWidget *parent) :
    QFrame(parent),
    ui(new Ui::AFrame)
{
    ui->setupUi(this);
}

AFrame::~AFrame()
{
    delete ui;
}

void AFrame::on_pushButton_clicked()
{
    emit signalReturn();
}
