#ifndef THREAD_H
#define THREAD_H

#include <QWidget>
#include <QStringList>
#include <QStringListModel>
#include <QListView>

#include <pthread.h>
#include <unistd.h>
#include <stdlib.h>
namespace Ui {
class Thread;
}

typedef struct {
    const char *name;
    QStringListModel *model;
    QListView *view;
} ThreadArg;



class Thread : public QWidget
{
    Q_OBJECT

public:
    explicit Thread(QWidget *parent = nullptr);
    ~Thread();
    QStringListModel *model;
    QStringListModel *modelA;
    QStringListModel *modelB;
    QStringListModel *modelC;

    ThreadArg *arg;
    ThreadArg *argA;
    ThreadArg *argB;
    ThreadArg *argC;

    ThreadArg args[3];


    pthread_t thread;

    static int index;

    static void* printThreadID(void*);
    static void* taskA(void* arg);
    static void* taskB(void* arg);

//    typedef void* (*pFUNC)(void *);
//    void* printThreadID(void* arg);
signals:

private slots:

    void on_ThreadCreate_clicked();

    void on_ThreadJoin_clicked();

private:
    Ui::Thread *ui;
};

#endif // THREAD_H
