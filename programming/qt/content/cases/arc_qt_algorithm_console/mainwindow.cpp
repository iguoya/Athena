#include "mainwindow.h"
#include "./ui_mainwindow.h"

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent)
//    , ui(new Ui::MainWindow)
{
    ui->setupUi(this);
//    ui->listView->setModel(&model);
//    ui->listView->setModel(&model);
    ui->tableView->setModel(&model);
    //    ui->tableView->horizontalHeader()->setSectionResizeMode(QHeaderView::Stretch);
    ui->treeView->setModel(&model);

    QList<QStandardItem *> row;
    m_parent = new QStandardItem("root");
    row.append(m_parent);
    model.appendRow(row);


    QMap<QPushButton*, QString> items = {
        {ui->rabbit, "RabbitA*"},
        {ui->fibonacci, "Rabbit*"},
        {ui->number, "NumberDigit*"},
        {ui->hanoi, "HanoiTower*"},
        {ui->binsearch, "BinSearch*"},
        {ui->gold, "Gold*"},
    };

    for(auto it = items.begin(); it != items.end(); ++it) {
        signalMapper.setMapping(it.key(), it.value());
        connect(it.key(), &QPushButton::clicked, &signalMapper,static_cast<void(QSignalMapper::*)()>(&QSignalMapper::map));

    }

    connect(&signalMapper, &QSignalMapper::mappedString, this, &MainWindow::run);
    on_random_clicked();
}

MainWindow::~MainWindow()
{
//    delete ui;
}

void MainWindow::run(const QString& name)
{
    int type = QMetaType::type(name.toLocal8Bit().data());
    Task *task = qobject_cast<Task*>(QMetaType::metaObjectForType(type)->newInstance());
    //    connect(task, &Task::display, ui->tabWidget, &QTabWidget::setCurrentIndex(2));
    connect(task, &Task::display, ui->textBrowser, &QTextBrowser::append);
    connect(task, &Task::displayList, this, &MainWindow::displayList);
    connect(task, &Task::setHeader, &model, &QStandardItemModel::setHorizontalHeaderLabels);
    connect(task, &Task::displayTable, this, &MainWindow::displayTable);
    connect(task, &Task::displayTree, this, &MainWindow::displayTree);

    task->setParent(m_parent);
    task->setNumber(ui->spinBox->value());
    task->setSeries(series);

    task->run();

    ui->treeView->expandAll();
}

void MainWindow::displayList(const QStringList &data)
{
//    ui->tabWidget->setCurrentIndex(0);
//    listModel.setStringList(data);
}


void MainWindow::displayTable(const QVector<QStringList>& data)
{
    //    tableModel.clear();
    ui->tabWidget->setCurrentIndex(1);
    for(auto row = 0; row < data.size(); ++row) {
        for(auto column = 0; column < data[row].size(); ++column) {
            //            tableModel.item(row, column)->setTextAlignment(Qt::AlignCenter);
            model.setItem(row, column, new QStandardItem(data[row][column]));
        }
    }

}

void MainWindow::displayTree()
{
    model.setHorizontalHeaderLabels(
                QStringList()<<QStringLiteral("层次") << QStringLiteral("名称")
                );     //设置列头
    for(int i=0;i<2;i++)
    {
        //一级节点，加入mModel
        QList<QStandardItem*> items1;
        QStandardItem* item1 = new QStandardItem(QString::number(i));
        QStandardItem* item2 = new QStandardItem(QStringLiteral("一级节点"));
        items1.append(item1);
        items1.append(item2);
        model.appendRow(items1);

        for(int j=0;j<5;j++)
        {
            //二级节点,加入第1个一级节点
            QList<QStandardItem*> items2;
            QStandardItem* item3 = new QStandardItem(QString::number(j));
            QStandardItem* item4 = new QStandardItem(QStringLiteral("二级节点"));
            items2.append(item3);
            items2.append(item4);
            item1->appendRow(items2);

            for(int k=0;k<5;k++)
            {
                //三级节点,加入第1个二级节点
                QList<QStandardItem*> items3;
                QStandardItem* item5 = new QStandardItem(QString::number(k));
                QStandardItem* item6 = new QStandardItem(QStringLiteral("三级节点"));
                items3.append(item5);
                items3.append(item6);
                item3->appendRow(items3);
            }
        }
    }
}

void MainWindow::on_random_clicked()
{
    series.clear();
    QStringList numbers;
    for(int i = 0; i < ui->spinBox_random->value(); ++i) {
        auto number = QRandomGenerator::global()->bounded(100);
        numbers<<QString::number(number);
        series.append(number);
    }
    ui->lineEdit->setText(numbers.join(", "));
}
