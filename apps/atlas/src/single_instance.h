#pragma once

#include <QLocalServer>
#include <QObject>
#include <QString>

class QWindow;

// 同一时刻只留一个 Atlas 进程。
//
// 编排器已经会在应用运行时改为前置窗口而不是再起一份（`athena-dev open`），这里
// 守的是绕过编排器的那条路：直接跑 build/atlas、或 Wayland 下编排器根本不被允许
// 抢焦点时，只能由应用自己响应「又被启动了一次」并把窗口举到前面。
class SingleInstance final : public QObject {
    Q_OBJECT

public:
    explicit SingleInstance(QString key, QObject* parent = nullptr);

    // 占住这个 key。返回 false 表示已经有一个实例在跑（已经请它前置窗口），
    // 调用方应当立刻退出。
    bool claim();

signals:
    // 又有人启动了一次：把现有窗口叫到前面。
    void presentRequested();

private:
    void onConnection();

    QString m_key;
    QLocalServer m_server;
};

// 把窗口举到前面。热重载会换窗口，所以取的是调用时的那一个。
void presentWindow(QWindow* window);
