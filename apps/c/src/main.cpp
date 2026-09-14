#include "curriculum.h"
#include "reloader.h"

#include <QFont>
#include <QGuiApplication>
#include <QQmlApplicationEngine>
#include <QQmlContext>
#include <QTimer>
#include <QUrl>
#include <cstdlib>

using namespace std;

namespace {

QString resolve_root() {
    if (const char* from_env = getenv("ATHENA_C_ROOT")) {
        if (from_env[0] != '\0') {
            return QString::fromUtf8(from_env);
        }
    }
    return QString::fromUtf8(ATHENA_C_SOURCE_ROOT);
}

} // namespace

int main(int argc, char* argv[]) {
    QGuiApplication app(argc, argv);
    app.setApplicationName("athena-c");
    app.setOrganizationName("Athena");
    // 与主程序学习页正文同一档：全局 22pt，QML 不再各自写小字号。
    QFont ui_font = app.font();
    ui_font.setPointSize(22);
    app.setFont(ui_font);

    const QString root = resolve_root();
    Curriculum curriculum(root);
    QQmlApplicationEngine engine;
    engine.addImportPath(root + "/qml");
    engine.rootContext()->setContextProperty("curriculum", &curriculum);
    engine.rootContext()->setContextProperty("appRoot", root);

    const QUrl main_qml = QUrl::fromLocalFile(root + "/qml/Main.qml");
    auto load = [&] {
        const QList<QObject*> roots = engine.rootObjects();
        for (QObject* object : roots) {
            object->deleteLater();
        }
        engine.clearComponentCache();
        curriculum.reload();
        engine.load(main_qml);
    };

    Reloader reloader(root, load);
    engine.load(main_qml);
    if (engine.rootObjects().isEmpty()) {
        return 1;
    }
    // 等窗口起来再监视：macOS 上 addPaths 会误触发一次 directoryChanged。
    QTimer::singleShot(400, &reloader, [&reloader] { reloader.watch(); });
    return app.exec();
}
