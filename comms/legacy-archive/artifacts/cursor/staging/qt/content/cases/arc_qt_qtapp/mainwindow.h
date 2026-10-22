#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>
//#include "QtAwesome/QtAwesome.h"
#include "system.h"
#include "thread.h"
#include <QLabel>

QT_BEGIN_NAMESPACE
namespace Ui { class MainWindow; }
QT_END_NAMESPACE

class MainWindow : public QMainWindow
{
    Q_OBJECT

public:
    MainWindow(QWidget *parent = nullptr);
    ~MainWindow();
//    QtAwesome* awesome;
    System system;

    Thread thread;

    QWidget *currentWindow;

private slots:

    void on_action_system_triggered();

    void on_action_thread_triggered();

    void on_action_process_triggered();

private:
    Ui::MainWindow *ui;
};
#endif // MAINWINDOW_H
