#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>
#include <QFile>
#include <QTextStream>
#include <QStringListModel>
#include <QStandardItemModel>
#include <QSignalMapper>
#include <QRandomGenerator>
#include <algorithm>
#include "task.h"

QT_BEGIN_NAMESPACE
namespace Ui { class MainWindow; }
QT_END_NAMESPACE

class MainWindow : public QMainWindow
{
    Q_OBJECT

public:
    MainWindow(QWidget *parent = nullptr);
    ~MainWindow();

private slots:
    void run(const QString &name);
    void displayList(const QStringList & data);
    void displayTable(const QVector<QStringList>& data);
    void displayTree();//const QVector<QStringList>& data

    void on_random_clicked();

private:

    Ui::MainWindow *ui;
    QSignalMapper signalMapper;

    QStringListModel listModel;
    QStandardItemModel model;

    QStandardItem *m_parent;

    QVector<int> series;//一组数据

};
#endif // MAINWINDOW_H
