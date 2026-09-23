#include "curriculum.h"
#include "reloader.h"

#include <QFont>
#include <QGuiApplication>
#include <QIcon>
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
    // 复用 app.json 里声明的同一份 icon.svg（读取源码而非打包资源，dev
    // 模式改图标不用重编）；标题栏与任务栏图标同出一源，不用另配一份通用图标。
    app.setWindowIcon(QIcon(root + "/icon.svg"));
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
