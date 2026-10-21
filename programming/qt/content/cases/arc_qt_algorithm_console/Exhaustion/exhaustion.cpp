#include "exhaustion.h"
#include "ui_exhaustion.h"

Exhaustion::Exhaustion(QWidget *parent) :
    QWidget(parent),
    ui(new Ui::Exhaustion)
{
    ui->setupUi(this);
}

Exhaustion::~Exhaustion()
{
    delete ui;
}
