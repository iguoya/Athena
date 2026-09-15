#include "atlas_catalog.h"
#include "single_instance.h"

#include <QFont>
#include <QGuiApplication>
#include <QQmlApplicationEngine>
#include <QQmlContext>
#include <QUrl>
#include <QWindow>

#include <cstdlib>

namespace {

QString resolveRoot() {
    if (const char* fromEnvironment = std::getenv("ATLAS_ROOT")) {
        if (*fromEnvironment != '\0') {
            return QString::fromUtf8(fromEnvironment);
        }
    }
    return QString::fromUtf8(ATLAS_SOURCE_ROOT);
}

} // namespace

int main(int argc, char* argv[]) {
    QGuiApplication application(argc, argv);
    application.setOrganizationName("Athena");
    application.setApplicationName("atlas");

    // 先问有没有人在跑，再做任何界面工作：第二次启动只是「把窗口叫到前面」。
    SingleInstance instance(QStringLiteral("athena.atlas"));
    if (!instance.claim()) {
        return 0;
    }

    QFont font = application.font();
    font.setPointSize(18);
    application.setFont(font);

    const QString root = resolveRoot();
    AtlasCatalog catalog(root);
    QQmlApplicationEngine engine;
    engine.addImportPath(root + "/qml");
    engine.rootContext()->setContextProperty("atlas", &catalog);
    engine.load(QUrl::fromLocalFile(root + "/qml/Main.qml"));
    if (engine.rootObjects().isEmpty()) {
        return 1;
    }

    QObject::connect(&instance, &SingleInstance::presentRequested, &application, [&engine] {
        presentWindow(qobject_cast<QWindow*>(engine.rootObjects().constFirst()));
    });

    return application.exec();
}
