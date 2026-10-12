// 建造者：Director 定步骤顺序，ConcreteBuilder 实现每一步。
// 实验：运行观察同一个 construct() 造出两种套餐。补 TODO：写一个 VegBuilder
// （主食 veggie burger、配菜 corn、饮料 tea），交给同一个 Director——
// Director 一行不改。
#include <iostream>
#include <string>
#include <vector>

class Meal {
public:
    void add(const std::string& item) { items.push_back(item); }
    void show() const { for (auto& i : items) std::cout << "- " << i << "\n"; std::cout << "\n"; }
private:
    std::vector<std::string> items;
};

class MealBuilder {
public:
    virtual ~MealBuilder() = default;
    virtual void buildMain() = 0;
    virtual void buildSide() = 0;
    virtual void buildDrink() = 0;
    virtual Meal getResult() = 0;
};
class ChickenBuilder : public MealBuilder {
    Meal m;
public:
    void buildMain()  override { m.add("chicken burger"); }
    void buildSide()  override { m.add("fries"); }
    void buildDrink() override { m.add("cola"); }
    Meal getResult()  override { return m; }
};
class FishBuilder : public MealBuilder {
    Meal m;
public:
    void buildMain()  override { m.add("fish burger"); }
    void buildSide()  override { m.add("salad"); }
    void buildDrink() override { m.add("juice"); }
    Meal getResult()  override { return m; }
};
// TODO(实验)：在这里新增 VegBuilder

class Director {
public:
    Meal construct(MealBuilder& b) {   // 步骤顺序固定，表示随 builder 而变
        b.buildMain(); b.buildSide(); b.buildDrink();
        return b.getResult();
    }
};

int main() {
    Director d;
    ChickenBuilder cb; FishBuilder fb;
    d.construct(cb).show();
    d.construct(fb).show();
    // TODO(实验)：VegBuilder vb; d.construct(vb).show();
}
