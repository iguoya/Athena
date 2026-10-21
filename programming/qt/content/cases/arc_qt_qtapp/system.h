#ifndef SYSTEM_H
#define SYSTEM_H

#include <QWidget>
#include <QStandardItemModel>
#include <QStringList>
#include <QStringListModel>
#include <ctype.h>
#include <stdlib.h>


namespace Ui {
class System;
}

class System : public QWidget
{
    Q_OBJECT

public:
    explicit System(QWidget *parent = nullptr);
    ~System();

    QStandardItemModel* model;

//    QList<QVector<QVariant>> sets;
signals:
//    void setLabels(QStringList columns);

//    void setData(QList<QVector<QVariant>> sets);
private slots:
    void on_Char_clicked();

    void on_String_clicked();

private:
    Ui::System *ui;
};

#endif // SYSTEM_H
