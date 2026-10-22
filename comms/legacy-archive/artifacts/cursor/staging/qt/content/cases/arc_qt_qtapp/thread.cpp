#include "thread.h"
#include "ui_thread.h"

int Thread::index;

Thread::Thread(QWidget *parent) :
    QWidget(parent),
    ui(new Ui::Thread)
{
    ui->setupUi(this);
    model = new QStringListModel;
    modelA = new QStringListModel;
    modelB = new QStringListModel;
    modelC = new QStringListModel;

    args[0] = { "线程A", modelA, ui->listView_2};
    args[1] = { "线程B", modelB, ui->listView_3};
    args[2] = { "线程C", modelC, ui->listView_4};

    //    connect(this, &Thread::setModel, ui->listView, )
    ui->listView->setModel(model);
    ui->listView_2->setModel(modelA);
    ui->listView_3->setModel(modelB);
    ui->listView_4->setModel(modelC);

}

Thread::~Thread()
{
    delete ui;
}

void* Thread::printThreadID(void* varg)
{
    ThreadArg* arg =  &((Thread *)varg)->args[index];

    ++index;

    QStringList data = {
        arg->name,
        QString("父进程id:%1").arg(getpid()),
        QString("线程id:%1 (%2)")
        .arg(pthread_self())
        .arg(QString::number(pthread_self(), 16).toUpper()),
    };

    for(int i = 1; i < 5; ++i) {
        data<<QString::number(i);
        sleep(rand()%3);
    }

    arg->model->setStringList(data);
    arg->view->setModel(arg->model);



    return NULL;
}

void *Thread::taskA(void *varg)
{
    ThreadArg* arg =  &((Thread *)varg)->args[0];

    QStringList data = {"线程A返回结果"};
    for(int i = 0; i < 10; ++i) {
        data<<QString::number(i);
        arg->model->setStringList(data);
        arg->view->setModel(arg->model);
        sleep(rand()%3);
    }

    return (void*)100;
}

void *Thread::taskB(void *varg)
{
    ThreadArg* arg =  &((Thread *)varg)->args[1];

    QStringList data = {"线程B返回结果"};
    for(int i = 0; i < 10; ++i) {
        data<<QString::number(i);
        arg->model->setStringList(data);
        arg->view->setModel(arg->model);
        sleep(rand()%3);
    }

    return (void*)10000;
}




void Thread::on_ThreadCreate_clicked()
{
    QStringList data {
        "父进程",
        QString("父进程id:%1").arg(getpid()),
                QString("线程id:%1 (%2)")
                .arg(pthread_self())
                .arg(QString::number(pthread_self(), 16).toUpper())
    };

    model->setStringList(data);



    arg = new ThreadArg;
    arg->name = "线程A";
    arg->model = modelA;
    arg->view = ui->listView_2;

    pthread_create(&thread, NULL, printThreadID, this);
    sleep(1);

    pthread_create(&thread, NULL, printThreadID, this);
    sleep(1);

    pthread_create(&thread, NULL, printThreadID, this);

}

void Thread::on_ThreadJoin_clicked()
{
    QStringList data;
    pthread_t threadA, threadB;
    void* resultA;
    void* resultB;
    pthread_create(&threadA, NULL, taskA, this);
    pthread_create(&threadB, NULL, taskB, this);

    pthread_join(threadA, &resultA);
    data<<QString::number((long)resultA);
    model->setStringList(data);



    pthread_join(threadB, &resultB);
    data<<QString::number((long)resultB);
    model->setStringList(data);
}
