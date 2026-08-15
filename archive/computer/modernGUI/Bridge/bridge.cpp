#include "bridge.h"

Bridge::Bridge(QObject *parent) : QObject(parent), m_message("Hello from C++")
{

}

QString Bridge::message() const {
    return m_message;
}

void Bridge::setMessage(const QString &message) {
    if (message != m_message) {
        m_message = message;
        emit messageChanged();
    }
}
