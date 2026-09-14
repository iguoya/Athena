#pragma once

#include <QObject>
#include <QFileSystemWatcher>
#include <QTimer>
#include <functional>

// 监视 qml/ 与 content/：教案改完保存就重新加载，不必重编 C++ 壳。
class Reloader : public QObject {
    Q_OBJECT

public:
    Reloader(QString root, std::function<void()> on_reload, QObject* parent = nullptr);

    void watch();

private:
    void schedule();

    QString m_root;
    std::function<void()> m_on_reload;
    QFileSystemWatcher m_watcher;
    QTimer m_debounce;
};
