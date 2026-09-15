#include "atlas_catalog.h"

#include <QtTest>

class AtlasCatalogTest final : public QObject {
    Q_OBJECT

private slots:
    void loadsAllMapsAndLaysOutAcyclicDependencies();
    void preservesStrictMapSelection();
    void defaultsToAnAcademicEntryMap();
    void everyNodeCarriesItsOwnPractice();
};

void AtlasCatalogTest::loadsAllMapsAndLaysOutAcyclicDependencies() {
    AtlasCatalog catalog(QString::fromUtf8(ATLAS_SOURCE_ROOT));
    QVERIFY2(catalog.error().isEmpty(), qPrintable(catalog.error()));
    QCOMPARE(catalog.maps().size(), 7);
    QCOMPARE(catalog.selectedMapId(), QStringLiteral("computer-practice"));
    QVERIFY(catalog.nodes().size() >= 6);
    QVERIFY(catalog.edges().size() >= 5);
    QVERIFY(catalog.canvasWidth() >= 1280);
    QVERIFY(catalog.canvasHeight() >= 720);
}

// 两张学科入口是底盘，方向图落在它上面；所以默认不能落在某个方向图上。
void AtlasCatalogTest::defaultsToAnAcademicEntryMap() {
    AtlasCatalog catalog(QString::fromUtf8(ATLAS_SOURCE_ROOT));
    QCOMPARE(catalog.selectedMapId(), QStringLiteral("computer-practice"));
    int academic = 0;
    for (const QVariant& value : catalog.maps()) {
        if (value.toMap().value("view_kind").toString() == "academic") {
            ++academic;
        }
    }
    QCOMPARE(academic, 2);
}

// 动手练习属于节点本身，不是另一张地图：把 practice 抽成独立实操图，会让同一个
// 能力域在侧栏里出现两次。这条断言就是防止再走回那条路。
void AtlasCatalogTest::everyNodeCarriesItsOwnPractice() {
    AtlasCatalog catalog(QString::fromUtf8(ATLAS_SOURCE_ROOT));
    for (const QVariant& mapValue : catalog.maps()) {
        const QVariantMap map = mapValue.toMap();
        catalog.openMap(map.value("id").toString());
        QVERIFY(!catalog.nodes().isEmpty());
        for (const QVariant& nodeValue : catalog.nodes()) {
            const QVariantMap node = nodeValue.toMap();
            QVERIFY2(!node.value("practice").toString().isEmpty(),
                     qPrintable(QStringLiteral("节点 %1 没有动手练习")
                                    .arg(node.value("id").toString())));
            QVERIFY(!node.value("validation").toString().isEmpty());
        }
    }
}

void AtlasCatalogTest::preservesStrictMapSelection() {
    AtlasCatalog catalog(QString::fromUtf8(ATLAS_SOURCE_ROOT));
    catalog.openMap("embedded-realtime");
    QCOMPARE(catalog.selectedMapId(), QStringLiteral("embedded-realtime"));
    catalog.selectNode("atlas.embedded.bringup");
    QCOMPARE(catalog.selectedNode().value("id").toString(), QStringLiteral("atlas.embedded.bringup"));
    catalog.openMap("aerospace-engineering");
    QVERIFY(catalog.selectedNode().isEmpty());
}

QTEST_MAIN(AtlasCatalogTest)
#include "atlas_catalog_test.moc"
