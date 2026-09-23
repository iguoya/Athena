#include "polaris_catalog.h"
#include "single_instance.h"

#include <QColorSpace>
#include <QDir>
#include <QFont>
#include <QFontDatabase>
#include <QGuiApplication>
#include <QIcon>
#include <QQmlApplicationEngine>
#include <QQmlContext>
#include <QQuickStyle>
#include <QQuickWindow>
#include <QSurfaceFormat>
#include <QStyleHints>
#include <QUrl>
#include <QWindow>

#include <cstdlib>

namespace {

QString tidyRoot(QString path) {
    path = path.trimmed();
    // Windows canonicalize 会带 \\?\ 前缀，QML 的 file URL 会变成 %3F，模块全部加载失败。
    if (path.startsWith(QLatin1String("\\\\?\\")) || path.startsWith(QLatin1String("//?/"))) {
        path = path.mid(4);
    }
    path.replace(QLatin1Char('\\'), QLatin1Char('/'));
    if (path.startsWith(QLatin1String("//?/"))) {
        path = path.mid(4);
    }
    return QDir::cleanPath(path);
}

QString resolveRoot() {
    if (const char* fromEnvironment = std::getenv("POLARIS_ROOT")) {
        if (*fromEnvironment != '\0') {
            return tidyRoot(QString::fromUtf8(fromEnvironment));
        }
    }
    return tidyRoot(QString::fromUtf8(POLARIS_SOURCE_ROOT));
}

QFont pickUiFont() {
    // 界面以中文为主。西文展示体（Segoe Variable Display）没有中文，系统会再
    // 拼一套回落字体，字重、字面和字距对不上，读起来就「瘦、散、不自然」。
    // 雅黑是同一套字里同时有中文和拉丁，中西混排才是一块字。
    const QStringList candidates = {
        QStringLiteral("Microsoft YaHei UI"),
        QStringLiteral("Microsoft YaHei"),
        QStringLiteral("PingFang SC"),
        QStringLiteral("Noto Sans CJK SC"),
        QStringLiteral("Noto Sans SC"),
    };
    QFont font;
    for (const QString& name : candidates) {
        if (QFontDatabase::hasFamily(name)) {
            font = QFont(name);
            break;
        }
    }
    font.setPointSize(16);
    font.setWeight(QFont::Medium);
    font.setHintingPreference(QFont::PreferDefaultHinting);
    font.setStyleStrategy(QFont::PreferAntialias);
    return font;
}

void configurePresentation() {
    // 4x MSAA 足够抗锯齿；8x 在整图离屏合成时会把交互拖成一顿一顿。
    QSurfaceFormat format;
    format.setRenderableType(QSurfaceFormat::DefaultRenderableType);
    format.setSwapBehavior(QSurfaceFormat::DoubleBuffer);
    format.setSwapInterval(1);
    format.setSamples(4);
    format.setDepthBufferSize(24);
    format.setStencilBufferSize(8);
    format.setColorSpace(QColorSpace(QColorSpace::SRgb));
    QSurfaceFormat::setDefaultFormat(format);

    QQuickWindow::setTextRenderType(QQuickWindow::QtTextRendering);
    QQuickStyle::setStyle(QStringLiteral("FluentWinUI3"));
}

} // namespace

int main(int argc, char* argv[]) {
    configurePresentation();

    QGuiApplication application(argc, argv);
    application.setOrganizationName("Athena");
    application.setApplicationName("polaris");
    application.setApplicationDisplayName(QStringLiteral("北极星"));
    const QString root = resolveRoot();
    // 复用 app.json 里声明的同一份 icon.svg；标题栏与任务栏图标同出一源，
    // 不用另配一份通用图标。
    application.setWindowIcon(QIcon(root + "/icon.svg"));
    if (QStyleHints* hints = application.styleHints()) {
        hints->setColorScheme(Qt::ColorScheme::Dark);
    }

    const QFont uiFont = pickUiFont();
    application.setFont(uiFont);

    SingleInstance instance(QStringLiteral("athena.polaris"));
    if (!instance.claim()) {
        return 0;
    }

    PolarisCatalog catalog(root);
    QQmlApplicationEngine engine;
    engine.addImportPath(root + "/qml");
    engine.rootContext()->setContextProperty("polaris", &catalog);
    engine.rootContext()->setContextProperty("uiFontFamily", uiFont.family());
    engine.load(QUrl::fromLocalFile(root + "/qml/Main.qml"));
    if (engine.rootObjects().isEmpty()) {
        return 1;
    }

    QObject::connect(&instance, &SingleInstance::presentRequested, &application, [&engine] {
        presentWindow(qobject_cast<QWindow*>(engine.rootObjects().constFirst()));
    });

    return application.exec();
}
