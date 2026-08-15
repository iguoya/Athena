#include <QGuiApplication>
#include <QQmlApplicationEngine>
#include <QQmlContext>
#include "Bridge/bridge.h"

int main(int argc, char *argv[])
{
    QCoreApplication::setAttribute(Qt::AA_EnableHighDpiScaling);

    QGuiApplication app(argc, argv);
//    QQuickStyle::setStyle("Imagine");

    qmlRegisterType<Bridge>("design.pattern", 1, 0, "Bridge");
    Bridge backend;


    QQmlApplicationEngine engine;
    const QUrl url(QStringLiteral("qrc:/main.qml"));
    engine.rootContext()->setContextProperty("backend", &backend);

    QObject::connect(&engine, &QQmlApplicationEngine::objectCreated,
                     &app, [url](QObject *obj, const QUrl &objUrl) {
        if (!obj && url == objUrl)
            QCoreApplication::exit(-1);
    }, Qt::QueuedConnection);
    engine.load(url);

    return app.exec();
}
