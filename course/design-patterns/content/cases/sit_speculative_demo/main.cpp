// 情境：夸夸其谈的通用性。为「以后可能支持更多格式」预先搭了接口、工厂、注册表和一堆
// 选项，可三年过去了，只有 CSV 一个实现，选项里一半从没人读。要读懂「导出一张表」，
// 得先穿过四层类。现在终于来了第二种格式 JSON——而这套脚手架并没有让它变容易。
// 重构手法：折叠继承体系（Collapse Hierarchy）、内联类（Inline Class）、改变函数声明
// （去掉没用的参数）、移除死代码（Remove Dead Code），《重构》第 2 版第 3 章
// 「夸夸其谈的通用性」。
//
// 实验：
// 1. 删掉 IExporter、ExporterFactory、ExporterRegistry、ExportOptions，
//    留下一个函数 std::string toCsv(const Table&)，输出与原来完全一致。
// 2. 新需求：写 std::string toJson(const Table&)，输出形如
//    [{"name":"apple","qty":3},{"name":"pear","qty":5}]
// 3. 解开 main 里的 TODO(实验) 行。看看新增一种格式现在要写多少行。
#include <iostream>
#include <map>
#include <memory>
#include <string>
#include <vector>

struct Row {
    std::string name;
    int qty;
};
using Table = std::vector<Row>;

struct ExportOptions {
    char delimiter = ',';
    bool header = true;
    std::string encoding = "utf-8";   // 没有任何代码读它
    int indent = 0;                   // 没有任何代码读它
};

class IExporter {
public:
    virtual ~IExporter() = default;
    virtual std::string run(const Table& table, const ExportOptions& options) const = 0;
};

class CsvExporter : public IExporter {
public:
    std::string run(const Table& table, const ExportOptions& options) const override {
        std::string out;
        if (options.header) out += std::string("name") + options.delimiter + "qty\n";
        for (const auto& r : table) out += r.name + options.delimiter + std::to_string(r.qty) + "\n";
        return out;
    }
};

class ExporterFactory {
public:
    virtual ~ExporterFactory() = default;
    virtual std::unique_ptr<IExporter> create() const = 0;
};

class CsvExporterFactory : public ExporterFactory {
public:
    std::unique_ptr<IExporter> create() const override { return std::make_unique<CsvExporter>(); }
};

class ExporterRegistry {
public:
    void add(const std::string& key, std::unique_ptr<ExporterFactory> f) { factories_[key] = std::move(f); }
    std::unique_ptr<IExporter> make(const std::string& key) const { return factories_.at(key)->create(); }
private:
    std::map<std::string, std::unique_ptr<ExporterFactory>> factories_;
};

int main() {
    Table table{{"apple", 3}, {"pear", 5}};
    ExporterRegistry registry;
    registry.add("csv", std::make_unique<CsvExporterFactory>());
    std::cout << registry.make("csv")->run(table, ExportOptions{});
    // TODO(实验)：折叠脚手架、写好 toCsv() 与 toJson() 后，把上面三行（registry 起）换成下面两行
    // std::cout << toCsv(table);
    // std::cout << toJson(table) << "\n";
}
