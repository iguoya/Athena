#include "binsearch.h"

size_t BinSearch::typeID = qRegisterMetaType<BinSearch*>("BinSearch");

BinSearch::BinSearch()
{

}

void BinSearch::run()
{
    setHeader({"查找key", "起始范围 index", "终止范围 index", "中间分割 index"});

    display(QString("原始序列: ")+vectorToString(m_series));

    key = m_number;
    display(QString("设置待查找Key值: %1").arg(key));

    std::sort(m_series.begin(), m_series.end());
    display(QString("数据有序后: ")+vectorToString(m_series));

    auto it = std::unique(m_series.begin(), m_series.end());
    m_series.erase(it, m_series.end());
    display(QString("数据去重后: ")+vectorToString(m_series));

    display(QString("二分查找： Key %1，位于位置：%2")
            .arg(key)
            .arg(binSearch(0, m_series.size()-1, key)));
    displayTable(table_result);
}

int BinSearch::binSearch(int start, int end, int key)
{
    if((start == end) && (m_series.at(start) != key)) {
        return -1;//找不到
    }
    int middle = (start+end) / 2;
    series_result.clear();
    series_result<< QString::number(key)
                 << QString::number(start)
                 << QString::number(end)
                 << QString::number(middle);

    table_result.append(series_result);
    if(m_series.at(middle) > key) {
        return binSearch(start, middle-1, key);
    } else if(m_series.at(middle) < key) {
        return binSearch(middle+1, end, key);
    } else if(m_series.at(middle) == key) {
        return middle+1;//现实位置+1
    }
    return -1;
}
