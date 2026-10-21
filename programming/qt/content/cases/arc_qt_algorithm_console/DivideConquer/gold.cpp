#include "gold.h"

size_t Gold::typeID = qRegisterMetaType<Gold*>("Gold");

Gold::Gold()
{

}

void Gold::run()
{

//    setTableHeader({"起始范围", "终止范围", "中间分割", "该组最大金块", "该组最小金块"});

    display(QString("金块原始序列: ")+vectorToString(m_series));

    displayTree();
}
