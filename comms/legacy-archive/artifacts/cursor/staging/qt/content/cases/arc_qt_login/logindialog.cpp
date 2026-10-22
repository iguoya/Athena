#include "logindialog.h"
#include "ui_logindialog.h"
#include "logindialog.h"
#include <QMessageBox>

LoginDialog::LoginDialog(QWidget *parent) :
    QDialog(parent),
    ui(new Ui::LoginDialog)
{
    ui->setupUi(this);
}

LoginDialog::~LoginDialog()
{
    delete ui;
}

void LoginDialog::on_loginBtn_clicked()
{
//    accept();
    if((ui->userLineEdit->text() == "tiger") &&
        ui->pwdLineEdit->text() == "guoya") {
        accept();
    } else {
        QMessageBox::warning(this, "登录失败", "用户名或者密码错误", QMessageBox::Yes);

        ui->userLineEdit->clear();
        ui->pwdLineEdit->clear();
        ui->userLineEdit->setFocus();
    }
}
