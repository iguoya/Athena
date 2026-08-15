#ifndef FACTORY_H
#define FACTORY_H
#include <functional>
#include <unordered_map>
#include <functional>
#include <vector>
#include <string>
#include "singleton.h"
//#include "product.h"
using namespace std;

using CreateObjectFunc = function<void*()>;
// 创建对象的回调函数
struct CreateObjectFuncClass {
    explicit CreateObjectFuncClass(CreateObjectFunc func) : create_func(func) {}
    CreateObjectFunc create_func;
};

// Object工厂类
class Factory : public Singleton<Factory> {
public:
    // 返回void *减少了代码的耦合
        // 提供给外部注册以及类创建
    void* CreateObject(const string& class_name) {
        CreateObjectFunc createobj = nullptr;

        if (create_funcs_.find(class_name) != create_funcs_.end())
            createobj = create_funcs_.find(class_name)->second->create_func;

        if (createobj == nullptr)
            return nullptr;

        // 调用函数指针指向的函数 调用REGISTER_CLASS中宏的绑定函数，也就是运行new className代码
        return createobj();
    }

        // 保存类名字符串到类对象构造函数指针的映射
    void RegisterObject(const string& class_name, CreateObjectFunc func) {
        auto it = create_funcs_.find(class_name);
        if (it != create_funcs_.end())
            create_funcs_[class_name]->create_func = func;
        else
            create_funcs_.emplace(class_name, new CreateObjectFuncClass(func));
    }

    ~Factory() {
        for (auto it : create_funcs_)
        {
            if (it.second != nullptr)
            {
                delete it.second;
                it.second = nullptr;
            }
        }
        create_funcs_.clear();
    }

private:
    // 缓存类名和生成类实例函数指针的map
    unordered_map<string, CreateObjectFuncClass* > create_funcs_;
};
#define REGISTERCLASS(className) \
class className##Helper { \
public: \
    className##Helper() \
    { \
        Factory::GetInstance()->RegisterObject(#className, []() \
        { \
            auto* obj = new className(); \
            return obj; \
        }); \
    } \
}; \
className##Helper g_##className##_helper;// 初始化一个helper的全局变量，执行构造函数中的RegisterObject执行。




#endif // FACTORY_H
