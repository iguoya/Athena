#ifndef AFRAME_H
#define AFRAME_H

#include <QFrame>

namespace Ui {
class AFrame;
}

class AFrame : public QFrame
{
    Q_OBJECT

public:
    explicit AFrame(QWidget *parent = nullptr);
    ~AFrame();

private slots:
    void on_pushButton_clicked();
signals:
    void signalReturn();
private:
    Ui::AFrame *ui;
};

#endif // AFRAME_H
