#ifndef SINGLETON_H
#define SINGLETON_H


// 单例类模板
template<typename T>
class Singleton
{
public:
    static T* GetInstance()
    {
        static T instance;
        return &instance;
    }

    Singleton(T&&) = delete;
    Singleton(const T&) = delete;
    void operator= (const T&) = delete;

protected:
    Singleton() = default;
    virtual ~Singleton() = default;
};


#endif // SINGLETON_H
