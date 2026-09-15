#include "atlas_catalog.h"

#include <QtTest>

class AtlasCatalogTest final : public QObject {
    Q_OBJECT

private slots:
    void loadsAllMapsAndLaysOutAcyclicDependencies();
    void preservesStrictMapSelection();
    void opensPairedPlaybookWithConcreteKit();
    void keepsRealtimeControlReferenceOffTheDefaultTrunk();
};

void AtlasCatalogTest::loadsAllMapsAndLaysOutAcyclicDependencies() {
    AtlasCatalog catalog(QString::fromUtf8(ATLAS_SOURCE_ROOT));
    QVERIFY2(catalog.error().isEmpty(), qPrintable(catalog.error()));
    QCOMPARE(catalog.maps().size(), 18);
    QCOMPARE(catalog.selectedMapId(), QStringLiteral("computer-practice"));
    QCOMPARE(catalog.selectedMapFamily(), QStringLiteral("system"));
    QVERIFY(catalog.nodes().size() >= 6);
    QVERIFY(catalog.edges().size() >= 5);
    QVERIFY(catalog.canvasWidth() >= 1280);
    QVERIFY(catalog.canvasHeight() >= 720);
}

void AtlasCatalogTest::keepsRealtimeControlReferenceOffTheDefaultTrunk() {
    AtlasCatalog catalog(QString::fromUtf8(ATLAS_SOURCE_ROOT));
    QCOMPARE(catalog.selectedMapId(), QStringLiteral("computer-practice"));
    catalog.openMap("control-17");
    QCOMPARE(catalog.selectedMapId(), QStringLiteral("control-17"));
    QCOMPARE(catalog.selectedCompanionMapId(), QStringLiteral("control-17-playbook"));
    catalog.openMap("robot-systems");
    QCOMPARE(catalog.selectedMapId(), QStringLiteral("robot-systems"));
    QCOMPARE(catalog.selectedCompanionMapId(), QStringLiteral("robot-playbook"));
}

void AtlasCatalogTest::opensPairedPlaybookWithConcreteKit() {
    AtlasCatalog catalog(QString::fromUtf8(ATLAS_SOURCE_ROOT));
    QCOMPARE(catalog.selectedCompanionMapId(), QStringLiteral("computer-playbook"));
    catalog.openMap("computer-playbook");
    QCOMPARE(catalog.selectedMapFamily(), QStringLiteral("playbook"));
    catalog.selectNode("atlas.play.cs.toolchain");
    const QVariantMap kit = catalog.selectedNode().value("kit").toMap();
    QVERIFY(!kit.value("reading").toString().isEmpty());
    QVERIFY(!kit.value("tooling").toString().isEmpty());
    QVERIFY(!kit.value("artifact").toString().isEmpty());
}

void AtlasCatalogTest::preservesStrictMapSelection() {
    AtlasCatalog catalog(QString::fromUtf8(ATLAS_SOURCE_ROOT));
    catalog.openMap("embedded-realtime");
    QCOMPARE(catalog.selectedMapId(), QStringLiteral("embedded-realtime"));
    catalog.selectNode("atlas.embedded.bringup");
    QCOMPARE(catalog.selectedNode().value("id").toString(), QStringLiteral("atlas.embedded.bringup"));
    catalog.openMap("vehicle-engineering");
    QVERIFY(catalog.selectedNode().isEmpty());
}

QTEST_MAIN(AtlasCatalogTest)
#include "atlas_catalog_test.moc"
