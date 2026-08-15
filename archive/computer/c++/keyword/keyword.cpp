#include "keyword.h"

Keyword::Keyword()
{

}

void Keyword::run()
{
    display("你好 中文!!!");
    vector<string> msgs = {
        "hello",
        "world",
        "china"
    };
    displays(msgs);


    vector<string> columns = {"芙", "蓉", "楼", "送", "辛", "渐", ""};

    vector<vector<string> > result = {
        {"寒", "雨", "连", "江", "夜", "入", "吴"},
        {"平", "明", "送", "客", "楚", "山", "孤"},
        {"洛", "阳", "亲", "友", "如", "相", "问"},
        {"一", "片", "冰", "心", "在", "玉", "壶"}
    };


    displayTable(columns, result);
}

