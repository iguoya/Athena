// 访问者：表示一个作用于对象结构中各元素的操作，可以在不改变元素类的前提下定义新操作。
// 改编自软设教程（第 5 版）例 7.7「馆藏文献统计」：一本 540 页的图书、两篇各 25 页的论文，
// 总页码 590。类名沿用教材。
// 实验：Book、Article 只提供 accept()；统计页数这个操作写在访问者里。
// 补 TODO：实现 LibrarySumPrintVisitor 的两个 visit()，把各自的页数累加进 sum_。
// 注意两个 visit 是按元素的具体类重载的——accept 里那句 visitor->visit(this) 完成了「双分派」。
#include <iostream>
#include <memory>
#include <string>
#include <vector>

class Book;
class Article;

// Visitor：为对象结构中每种具体元素声明一个 visit 操作
class LibraryVisitor {
public:
    virtual ~LibraryVisitor() = default;
    virtual void visit(Book* p_book) = 0;
    virtual void visit(Article* p_article) = 0;
    virtual void printSum() = 0;
};

// Element：定义以访问者为参数的 accept 操作
class LibraryItemInterface {
public:
    virtual ~LibraryItemInterface() = default;
    virtual void accept(LibraryVisitor* visitor) = 0;
};

// ConcreteElement：论文，页数 = 结束页 - 起始页
class Article : public LibraryItemInterface {
public:
    Article(std::string author, std::string title, int start_page, int end_page)
        : m_title(std::move(title)), m_author(std::move(author)), m_start_page(start_page), m_end_page(end_page) {}
    int getNumberOfPages() const { return m_end_page - m_start_page; }
    void accept(LibraryVisitor* visitor) override { visitor->visit(this); }
private:
    std::string m_title, m_author;
    int m_start_page, m_end_page;
};

// ConcreteElement：图书
class Book : public LibraryItemInterface {
public:
    Book(std::string author, std::string title, int pages)
        : m_title(std::move(title)), m_author(std::move(author)), m_pages(pages) {}
    int getNumberOfPages() const { return m_pages; }
    void accept(LibraryVisitor* visitor) override { visitor->visit(this); }
private:
    std::string m_title, m_author;
    int m_pages;
};

// ConcreteVisitor：统计总页数，局部状态 sum_ 在遍历中累积
class LibrarySumPrintVisitor : public LibraryVisitor {
public:
    void visit(Book* p_book) override {
        // TODO(实验)：把图书的页数累加进 sum_
        (void)p_book;
    }
    void visit(Article* p_article) override {
        // TODO(实验)：把论文的页数累加进 sum_
        (void)p_article;
    }
    void printSum() override { std::cout << "SUM = " << sum_ << "\n"; }
private:
    int sum_ = 0;
};

int main() {
    // ObjectStructure：能枚举它的元素
    std::vector<std::unique_ptr<LibraryItemInterface>> library;
    library.push_back(std::make_unique<Book>("author1", "book1", 540));
    library.push_back(std::make_unique<Article>("author2", "paper1", 1, 26));
    library.push_back(std::make_unique<Article>("author3", "paper2", 10, 35));

    LibrarySumPrintVisitor visitor;
    for (auto& item : library) item->accept(&visitor);
    visitor.printSum();
}
