#include "reloader.h"

#include <QDirIterator>

using namespace std;

Reloader::Reloader(QString root, std::function<void()> on_reload, QObject* parent)
    : QObject(parent), m_root(std::move(root)), m_on_reload(std::move(on_reload)) {
    m_debounce.setSingleShot(true);
    m_debounce.setInterval(160);
    connect(&m_debounce, &QTimer::timeout, this, [this] {
        watch();
        if (m_on_reload) {
            m_on_reload();
        }
    });
    connect(&m_watcher, &QFileSystemWatcher::fileChanged, this, [this](const QString&) {
        schedule();
    });
    connect(
        &m_watcher, &QFileSystemWatcher::directoryChanged, this, [this](const QString&) {
            schedule();
        });
}

void Reloader::watch() {
    const QStringList old = m_watcher.files() + m_watcher.directories();
    if (!old.isEmpty()) {
        m_watcher.removePaths(old);
    }

    const QStringList roots = {m_root + "/qml", m_root + "/content"};
    QStringList paths;
    for (const QString& root : roots) {
        paths.push_back(root);
        QDirIterator it(
            root, QStringList() << "*.qml" << "*.json", QDir::Files,
            QDirIterator::Subdirectories);
        while (it.hasNext()) {
            paths.push_back(it.next());
        }
    }
    if (!paths.isEmpty()) {
        m_watcher.addPaths(paths);
    }
}

void Reloader::schedule() {
    m_debounce.start();
}
