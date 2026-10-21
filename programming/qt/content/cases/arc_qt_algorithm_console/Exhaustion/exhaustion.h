#ifndef EXHAUSTION_H
#define EXHAUSTION_H

#include <QWidget>

namespace Ui {
class Exhaustion;
}

class Exhaustion : public QWidget
{
    Q_OBJECT

public:
    explicit Exhaustion(QWidget *parent = nullptr);
    ~Exhaustion();

private:
    Ui::Exhaustion *ui;
};

#endif // EXHAUSTION_H
