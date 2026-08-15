#include "factory.h"

//void *Factory::CreateProduct(const string &name)
//{
//    Address address = nullptr;

//    if (products.find(name) != products.end())
//        address = products.find(name)->second->address;

//    // 调用函数指针指向的函数 调用REGISTER_CLASS中宏的绑定函数，也就是运行new className代码
//    return address();
//}

//void Factory::RegisterProduct(const string &name, Address address)
//{

//    auto it = products.find(name);
//    if (it != products.end())
//        products[name]->address = address;
//    else
//        products.emplace(name, new ProductClass(address));


//}

//Factory::~Factory()
//{

//    for (auto it : products)
//    {
//        if (it.second != nullptr)
//        {
//            delete it.second;
//            it.second = nullptr;
//        }
//    }
//    products.clear();

//}


//Factory::Factory()
//{

//}

//Product *Factory::create(ProductType e)
//{
//    switch(e) {
//    case kHelloWorld:
//        return new HelloWorld;
//    case kAuto:
//        return new Auto;
//    case kStatic:
//    case kConst:
//        return new Const;
//    case kFunctionPointer:
//        return new FunctionPointer;
//    }
//    return new Const;
//}

//Factory::~Factory()
//{

//}
