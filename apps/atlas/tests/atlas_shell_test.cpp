#include "single_instance.h"

#include <QCoreApplication>
#include <QSignalSpy>
#include <QtTest>

class AtlasShellTest final : public QObject {
    Q_OBJECT

private slots:
    void secondInstanceDefersToTheFirst();
    void reclaimsKeyLeftBehindByACrash();
};

void AtlasShellTest::secondInstanceDefersToTheFirst() {
    // 同一台机器上可能并行跑着别的测试，key 带上 pid 才不互相抢。
    const QString key =
        QStringLiteral("athena.atlas.test.%1").arg(QCoreApplication::applicationPid());

    SingleInstance first(key);
    QVERIFY(first.claim());
    QSignalSpy presented(&first, &SingleInstance::presentRequested);

    SingleInstance second(key);
    QVERIFY(!second.claim());
    // 第二份不开窗口，而是让第一份把自己举到前面。
    QVERIFY(presented.wait(2000));
}

void AtlasShellTest::reclaimsKeyLeftBehindByACrash() {
    const QString key =
        QStringLiteral("athena.atlas.stale.%1").arg(QCoreApplication::applicationPid());
    {
        SingleInstance crashed(key);
        QVERIFY(crashed.claim());
    }
    // 上一次异常退出会在 Unix 上留下套接字文件；不清掉它，应用就再也起不来了。
    SingleInstance next(key);
    QVERIFY(next.claim());
}

QTEST_GUILESS_MAIN(AtlasShellTest)
#include "atlas_shell_test.moc"
