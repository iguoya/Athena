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
    void bindsNecessityToCareerTargets();
    void keepsCrossMapDependenciesReachable();
    void restoresCppKnowledgeGraphAsTwoChapters();
    void locksCareerMapsUntilKnowledgeSystemIsComplete();
};

void AtlasCatalogTest::loadsAllMapsAndLaysOutAcyclicDependencies() {
    AtlasCatalog catalog(QString::fromUtf8(ATLAS_SOURCE_ROOT));
    QVERIFY2(catalog.error().isEmpty(), qPrintable(catalog.error()));
    QCOMPARE(catalog.maps().size(), 18);
    QCOMPARE(catalog.selectedMapId(), QStringLiteral("computer-science"));
    QVERIFY(catalog.nodes().size() >= 15);
    QVERIFY(catalog.edges().size() >= 13);
    QVERIFY(catalog.canvasWidth() >= 1280);
    QVERIFY(catalog.canvasHeight() >= 720);
}

// 三层各自独立：学科入口是底盘，职业方向是大方向，职业目标是落点。默认要落在
// 学科入口上，不能落在方向图或目标图上。
void AtlasCatalogTest::defaultsToAnAcademicEntryMap() {
    AtlasCatalog catalog(QString::fromUtf8(ATLAS_SOURCE_ROOT));
    QCOMPARE(catalog.selectedMapId(), QStringLiteral("computer-science"));
    QHash<QString, int> byKind;
    for (const QVariant& value : catalog.maps()) {
        ++byKind[value.toMap().value("view_kind").toString()];
    }
    // 课程知识图谱恢复为计算机 / 电子信息两章，实践主干两张仍在（ADR 0010）。
    QCOMPARE(byKind.value("academic"), 4);
    QCOMPARE(byKind.value("target"), 9);
    QCOMPARE(byKind.value("career") + byKind.value("engineering"), 5);
}

// 必要程度要能追到它支撑的目标能力（ADR 0009 第 5 条）。只给等级会退化成口味
// 排序，所以等级、理由、目标三者必须同时在场，且目标必须真的指向目标层。
void AtlasCatalogTest::bindsNecessityToCareerTargets() {
    AtlasCatalog catalog(QString::fromUtf8(ATLAS_SOURCE_ROOT));
    QSet<QString> targetMapIds;
    for (const QVariant& value : catalog.maps()) {
        const QVariantMap map = value.toMap();
        if (map.value("view_kind").toString() == "target") {
            targetMapIds.insert(map.value("id").toString());
        }
    }
    QCOMPARE(targetMapIds.size(), 9);

    for (const QVariant& mapValue : catalog.maps()) {
        const QVariantMap map = mapValue.toMap();
        if (map.value("view_kind").toString() != QStringLiteral("academic")) {
            continue;
        }
        for (const QVariant& nodeValue : map.value("nodes").toList()) {
            const QVariantMap node = nodeValue.toMap();
            const QString nodeId = node.value("id").toString();
            QVERIFY2(!node.value("pitfall").toString().isEmpty(),
                     qPrintable(QStringLiteral("节点 %1 没写难点").arg(nodeId)));
            QVERIFY2(!node.value("priority_reason").toString().isEmpty(),
                     qPrintable(QStringLiteral("节点 %1 没写必要程度的理由").arg(nodeId)));
            const QStringList targets = node.value("targets").toStringList();
            QVERIFY2(!targets.isEmpty(),
                     qPrintable(QStringLiteral("节点 %1 没有 targets").arg(nodeId)));
            for (const QString& target : targets) {
                QVERIFY2(targetMapIds.contains(target),
                         qPrintable(QStringLiteral("节点 %1 的 targets 指向了非目标层地图 %2")
                                        .arg(nodeId, target)));
            }
        }
    }
}

// 拆成八张图之后，一部分先修关系的两端落在不同图里。它们放在顶层 cross_edges，
// 界面要能顺着它跳到对端——否则这些依赖等于因为拆图而消失了（ADR 0009 第 6 条）。
void AtlasCatalogTest::keepsCrossMapDependenciesReachable() {
    AtlasCatalog catalog(QString::fromUtf8(ATLAS_SOURCE_ROOT));
    // C 语言在程序设计图、51 单片机在单片机图，这条强先修必须还在。
    const QVariantList links = catalog.crossEdgesFor(QStringLiteral("atlas.ei.mcu_8051"));
    QVERIFY(!links.isEmpty());
    bool foundCLanguage = false;
    for (const QVariant& value : links) {
        const QVariantMap link = value.toMap();
        QVERIFY(!link.value("rationale").toString().isEmpty());
        // 对端必须能定位到某张图，否则界面上点不过去。
        QVERIFY(!link.value("map_id").toString().isEmpty());
        QVERIFY(!link.value("peer_title").toString().isEmpty());
        if (link.value("peer_id").toString() == QStringLiteral("atlas.cs.c_lang")) {
            foundCLanguage = true;
            QVERIFY(link.value("incoming").toBool());
            QVERIFY(link.value("strong").toBool());
        }
    }
    QVERIFY(foundCLanguage);
}

// 界面上不出现具体院所名，一律用「某所」（仓库级 ADR 0055）。这条断言盯着内容
// 文件本身，因为淡化一旦只做在 QML 里，下一次换渲染方式就会把它漏掉。
//
// 禁用词写成 Unicode 转义：直接写字面量，这个文件自己就成了下一个命中点，
// 全仓扫描（scripts/check.py）会把检查代码误报成违规内容。
void AtlasCatalogTest::keepsUnitNamesOutOfTheContent() {
    QFile file(QString::fromUtf8(ATLAS_SOURCE_ROOT) + "/content/atlas.json");
    QVERIFY(file.open(QIODevice::ReadOnly | QIODevice::Text));
    const QString text = QString::fromUtf8(file.readAll());
    QVERIFY(!text.contains(QString::fromUtf8("\u5341\u4e03\u6240")));
    QVERIFY(!text.contains(QString::fromUtf8("\u56db\u9662")));
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

// 原 C++ 首页知识图谱是计算机 / 电子信息两张完整图。拆成六张碎片会把同侧
// 先修变成跨图跳转，也会把虚线来路误写成强先修（ADR 0010）。
void AtlasCatalogTest::restoresCppKnowledgeGraphAsTwoChapters() {
    AtlasCatalog catalog(QString::fromUtf8(ATLAS_SOURCE_ROOT));
    QVERIFY2(catalog.error().isEmpty(), qPrintable(catalog.error()));

    catalog.openMap("computer-science");
    QCOMPARE(catalog.nodes().size(), 15);
    QVERIFY(catalog.edges().size() >= 13);
    catalog.selectNode("atlas.cs.cpp");
    QCOMPARE(catalog.selectedNode().value("entry").toBool(), true);
    QCOMPARE(catalog.selectedNode().value("verify").toString(), QStringLiteral("code"));
    QVERIFY(catalog.selectedNode().value("requires").toList().isEmpty());

    bool foundWeakCppOrigin = false;
    for (const QVariant& value : catalog.edges()) {
        const QVariantMap edge = value.toMap();
        if (edge.value("from").toString() == QStringLiteral("atlas.cs.c_lang")
            && edge.value("to").toString() == QStringLiteral("atlas.cs.cpp")) {
            QCOMPARE(edge.value("relation").toString(), QStringLiteral("enables"));
            QVERIFY(edge.value("number").toInt() >= 1);
            foundWeakCppOrigin = true;
        }
    }
    QVERIFY(foundWeakCppOrigin);

    catalog.openMap("electronic-information");
    QCOMPARE(catalog.nodes().size(), 13);
    catalog.selectNode("atlas.ei.electronics_basics");
    QCOMPARE(catalog.selectedNode().value("entry").toBool(), true);
    QCOMPARE(catalog.selectedNode().value("verify").toString(), QStringLiteral("bench"));
}

// 职业图仍在内容里（宁增勿删），但当前盘面只开放技术体系（ADR 0012）。
void AtlasCatalogTest::locksCareerMapsUntilKnowledgeSystemIsComplete() {
    AtlasCatalog catalog(QString::fromUtf8(ATLAS_SOURCE_ROOT));
    QVERIFY(!catalog.mapLocked(QStringLiteral("computer-science")));
    QVERIFY(!catalog.mapLocked(QStringLiteral("electronic-information")));
    QVERIFY(!catalog.mapLocked(QStringLiteral("computer-practice")));
    QVERIFY(!catalog.mapLocked(QStringLiteral("electronic-practice")));
    QVERIFY(catalog.mapLocked(QStringLiteral("embedded-realtime")));
    QVERIFY(catalog.mapLocked(QStringLiteral("aerospace-engineering")));
    QVERIFY(catalog.mapLocked(QStringLiteral("target-realtime-software")));
    QVERIFY(catalog.mapLocked(QStringLiteral("large-model-engineering")));
}

QTEST_MAIN(AtlasCatalogTest)
#include "atlas_catalog_test.moc"
