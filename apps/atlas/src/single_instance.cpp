#include "single_instance.h"

#include <QDebug>
#include <QLocalSocket>
#include <QWindow>

#include <utility>

namespace {

constexpr int kHandshakeMs = 300;

} // namespace

SingleInstance::SingleInstance(QString key, QObject* parent)
    : QObject(parent), m_key(std::move(key)) {
    connect(&m_server, &QLocalServer::newConnection, this, &SingleInstance::onConnection);
}

bool SingleInstance::claim() {
    QLocalSocket probe;
    probe.connectToServer(m_key);
    if (probe.waitForConnected(kHandshakeMs)) {
        // 连上了就说明先来的那份还活着。连接本身就是信号，不必约定报文格式。
        probe.disconnectFromServer();
        return false;
    }

    // 上一次异常退出会在 Unix 上留下套接字文件，不清掉 listen 会一直失败。
    QLocalServer::removeServer(m_key);
    if (!m_server.listen(m_key)) {
        // 守卫起不来只影响「第二次启动能否前置窗口」，不该拦住应用本身。
        qWarning().noquote() << "Atlas 单实例守卫没能监听：" << m_server.errorString();
    }
    return true;
}

void SingleInstance::onConnection() {
    while (QLocalSocket* socket = m_server.nextPendingConnection()) {
        connect(socket, &QLocalSocket::disconnected, socket, &QLocalSocket::deleteLater);
        socket->disconnectFromServer();
    }
    emit presentRequested();
}

void presentWindow(QWindow* window) {
    if (window == nullptr) {
        return;
    }
    if (window->windowStates().testFlag(Qt::WindowMinimized)) {
        window->setWindowStates(Qt::WindowNoState);
    }
    window->show();
    window->raise();
    window->requestActivate();
}
