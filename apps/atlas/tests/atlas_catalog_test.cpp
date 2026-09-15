#include "atlas_catalog.h"

#include <QtTest>

class AtlasCatalogTest final : public QObject {
    Q_OBJECT

private slots:
    void loadsAllMapsAndLaysOutAcyclicDependencies();
    void preservesStrictMapSelection();
    void defaultsToAnAcademicEntryMap();
    void keepsUnitNamesOutOfTheContent();
    void everyNodeCarriesItsOwnPractice();
};

void AtlasCatalogTest::loadsAllMapsAndLaysOutAcyclicDependencies() {
    AtlasCatalog catalog(QString::fromUtf8(ATLAS_SOURCE_ROOT));
    QVERIFY2(catalog.error().isEmpty(), qPrintable(catalog.error()));
    QCOMPARE(catalog.maps().size(), 16);
    QCOMPARE(catalog.selectedMapId(), QStringLiteral("computer-practice"));
    QVERIFY(catalog.nodes().size() >= 6);
    QVERIFY(catalog.edges().size() >= 5);
    QVERIFY(catalog.canvasWidth() >= 1280);
    QVERIFY(catalog.canvasHeight() >= 720);
}

// 三层各自独立：学科入口是底盘，职业方向是大方向，职业目标是落点。默认要落在
// 学科入口上，不能落在方向图或目标图上。
void AtlasCatalogTest::defaultsToAnAcademicEntryMap() {
    AtlasCatalog catalog(QString::fromUtf8(ATLAS_SOURCE_ROOT));
    QCOMPARE(catalog.selectedMapId(), QStringLiteral("computer-practice"));
    QHash<QString, int> byKind;
    for (const QVariant& value : catalog.maps()) {
        ++byKind[value.toMap().value("view_kind").toString()];
    }
    QCOMPARE(byKind.value("academic"), 2);
    QCOMPARE(byKind.value("target"), 9);
    QCOMPARE(byKind.value("career") + byKind.value("engineering"), 5);
}

// 界面上不出现具体单位名。这条断言盯着内容文件本身，因为淡化一旦只做在 QML 里，
// 下一次换渲染方式就会把它漏掉。
void AtlasCatalogTest::keepsUnitNamesOutOfTheContent() {
    QFile file(QString::fromUtf8(ATLAS_SOURCE_ROOT) + "/content/atlas.json");
    QVERIFY(file.open(QIODevice::ReadOnly | QIODevice::Text));
    const QString text = QString::fromUtf8(file.readAll());
    QVERIFY(!text.contains(QStringLiteral("十七所")));
    QVERIFY(!text.contains(QStringLiteral("四院")));
    QVERIFY(text.contains(QStringLiteral("某所")));
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
