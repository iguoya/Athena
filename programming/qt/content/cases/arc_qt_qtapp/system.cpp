#include "system.h"
#include "ui_system.h"

System::System(QWidget *parent) :
    QWidget(parent),
    ui(new Ui::System)
{
    ui->setupUi(this);

    ui->tableView->horizontalHeader()->setSectionResizeMode(QHeaderView::ResizeToContents); // 表格宽度随内容自动扩展
    ui->tableView->horizontalHeader()->setSectionResizeMode(QHeaderView::Stretch); // 表格宽度自动根据UI进行计算，不可手动调整宽度
    ui->tableView->setAlternatingRowColors(true);  // 开启隔行异色


    model = new QStandardItemModel();
    //    model->setHorizontalHeaderLabels({"测试名称", "输入", "结果"});
    ui->tableView->setModel(model);

    model = new QStandardItemModel;
}

System::~System()
{
    delete ui;
}

//void TableView::setModelNames(QStringList names)
//{
//    for(int i = 0; i< names.size(); ++i) {
//        model->setHorizontalHeaderItem(i, new QStandardItem(names.at(i)));
//    }
//    ui->tableView->setModel(model);
//}

//void TableView::setData(QList<QVector<QVariant>> sets)
//{
//    model->clear();
//    for(auto record : sets) {
//        QList<QStandardItem *> row;
//        for(auto item : record) {
//            row.append(new QStandardItem(item.toString()));
//        }
//        model->appendRow(row);
//    }
//}




void System::on_Char_clicked()
{

    model->clear();

    for(int i = 0; i <= 127; ++i) {
        QList<QStandardItem *> row;
        row.append(new QStandardItem(QString("%1").arg(i)));
        if(isprint(i)) {
            row.append(new QStandardItem(QString("%1").arg(QChar(i))));
            row.append(new QStandardItem(QString::number(i, 16).toUpper()));
        }
        if(ispunct(i)){
            row.append(new QStandardItem("标点符号"));
        }
        if(isdigit(i)) {
            row.append(new QStandardItem("阿拉伯数字"));
        }
        if(isalpha(i)) {
            row.append(new QStandardItem("拉丁字符"));
        }
        if(isupper(i)) {
            row.append(new QStandardItem("大写字符"));
        }
        if(islower(i)) {
            row.append(new QStandardItem("小写字符"));
        }
        if(isspace(i)) {
            row.append(new QStandardItem("空白字符"));
        }
        if(isascii(i)) {
            row.append(new QStandardItem("ASCII码"));
        }
        model->appendRow(row);
    }
    ui->tableView->setModel(model);
}

void System::on_String_clicked()
{
    model->clear();

    //    QList<QStandardItem *> row;
    //    QString
    //    model->appendRow()
    //    model->Str
    QList<QStandardItem *> row;
    const char *s1 = "3.1416xx33x";

    row = {
        new QStandardItem(s1),
        new QStandardItem("atoi"),
        new QStandardItem(QString("%1").arg(atoi(s1)))
    };
    model->appendRow(row);

    row = {
        new QStandardItem(s1),
        new QStandardItem("atof"),
        new QStandardItem(QString("%1").arg(atof(s1)))
    };
    model->appendRow(row);


    const char *s2 = "22222222.333333ccc";
    row = {
        new QStandardItem(s2),
        new QStandardItem("atoi"),
        new QStandardItem(QString("%1").arg(atoi(s2)))
    };
    model->appendRow(row);




    const char *s3 = "222232222333.3333339999ccc";
    row = {
        new QStandardItem(s3),
        new QStandardItem("atod"),
        new QStandardItem(QString("%1").arg(strtod(s3, NULL)))
    };
    model->appendRow(row);



    const char *s4 = "china我是中国人";
    row = {
        new QStandardItem(s4),
        new QStandardItem("strlen"),
        new QStandardItem(QString("%1").arg(strlen(s4)))
    };
    model->appendRow(row);


    const char *s5 = "abcdefg";
    row = {
        new QStandardItem(s5),
        new QStandardItem("index"),
        new QStandardItem(QString("%1").arg(index(s5, 'e')))
    };
    model->appendRow(row);



    const char *s6 = "abcdefg";
    const char *s7 = "xyz";
    char s8[100] = {0};
    row = {
        new QStandardItem(s6),
        new QStandardItem(s7),
        new QStandardItem("strcpy"),
        new QStandardItem(strcpy(s8, s6)),
        new QStandardItem("strncpy"),
        new QStandardItem(strncpy(s8, s7, strlen(s7)))
    };
    model->appendRow(row);



    const char *s61 = "abcdefg";
    const char *s71 = "hijklmno";
    char s81[100] = {0};

    row = {
        new QStandardItem(s61),
        new QStandardItem(s71),
        new QStandardItem("strcat"),
        new QStandardItem(strcat(s81, s61)),
        new QStandardItem(strncat(s81, s71, strlen(s71)))
    };
    model->appendRow(row);




    const char *s9 = "abcdefg";
    char *sp = strdup("abcdefg");
    sp[1] = 'x';

    row = {
        new QStandardItem(s9),
        new QStandardItem("strdup"),
        new QStandardItem(sp),
    };
    free(sp);
    model->appendRow(row);




    const char *s10 = "abcdefg";
    const char *s11 = "abcdefg";
    const char *s12 = "hijklmn";
    row = {
        new QStandardItem(s10),
        new QStandardItem(s11),
        new QStandardItem(s12),
        new QStandardItem("strcmp"),
        new QStandardItem(strcmp(s10, s11)),
        new QStandardItem(strcmp(s10, s12)),
    };
    model->appendRow(row);




    const char *s13 = "abcdefg";
    const char *s14 = "efg";
    const char *s15 = "xyz";

    char msg[20] = {0};
    if(strstr(s13, s15) != NULL) {
        strcpy(msg, "找到");
    } else {
        strcpy(msg, "没有找到");
    }

    row = {
        new QStandardItem(s13),
        new QStandardItem(s14),
        new QStandardItem(s15),
        new QStandardItem("strstr"),
        new QStandardItem(strstr(s13, s14)),
        new QStandardItem(msg),
    };
    model->appendRow(row);




    char s16[100] = "abc;dessk;kccfg";

    row = {
        new QStandardItem(s16),
        new QStandardItem("strstr"),
        new QStandardItem(strtok(s16, ";")),
        new QStandardItem(strtok(s16, "b")),
    };
    model->appendRow(row);

    ui->tableView->setModel(model);
}
