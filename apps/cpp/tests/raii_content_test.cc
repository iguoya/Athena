#include "raii/raii.hpp"

#include <gtest/gtest.h>

#include <sstream>

namespace {

using Experiment = void (RAII::*)(ostream&) const;

string run_experiment(Experiment experiment) {
    RAII chapter;
    ostringstream output;
    (chapter.*experiment)(output);
    return output.str();
}

TEST(RaiiContentTest, ReleasesScopedResourceDuringExceptionUnwinding) {
    EXPECT_EQ(
        run_experiment(&RAII::basic),
        "构造对象后资源可用: 42\n"
        "作用域内资源已释放: 否\n"
        "捕获异常: 模拟异常\n"
        "异常离开作用域后资源已释放: 是\n");
}

TEST(RaiiContentTest, TransfersUniqueOwnershipAndDestroysExactlyOnce) {
    EXPECT_EQ(
        run_experiment(&RAII::unique),
        "创建后持有: 独占资源\n"
        "unique_ptr 可拷贝: 否\n"
        "所有权转移后原指针为空: 是\n"
        "新指针持有: 独占资源\n"
        "离开作用域后析构次数: 1\n");
}

TEST(RaiiContentTest, SharesOwnershipUntilTheLastOwnerLeaves) {
    EXPECT_EQ(
        run_experiment(&RAII::shared),
        "第一个持有者创建后 use_count: 1\n"
        "复制 shared_ptr 后 use_count: 2\n"
        "两个指针访问同一对象: 是\n"
        "第二个持有者销毁后 use_count: 1\n"
        "对象已析构: 否\n"
        "最后持有者销毁后析构次数: 1\n"
        "控制块观察到对象已过期: 是\n"
        "提示: make_shared 通常把对象和控制块合并为一次分配；"
        "引用计数安全不等于对象线程安全。\n");
}

TEST(RaiiContentTest, UsesWeakOwnershipToBreakTheBackReference) {
    EXPECT_EQ(
        run_experiment(&RAII::weak),
        "纯 shared_ptr 循环在外部持有者离开后仍存活: 是\n"
        "手动拆环后析构节点数: 2\n"
        "反向 weak_ptr 不增加前驱计数: 1\n"
        "后继由局部变量和前驱共同拥有，计数: 2\n"
        "局部后继释放后 lock 成功: 是\n"
        "拥有者全部离开后析构节点数: 2\n"
        "对象销毁后 lock 返回空: 是\n");
}

TEST(RaiiContentTest, SelectsReferenceOverloadsByValueCategory) {
    EXPECT_EQ(
        run_experiment(&RAII::rvalue),
        "具名可修改对象选择: 左值引用\n"
        "具名 const 对象选择: const 左值引用\n"
        "临时对象选择: 右值引用\n"
        "std::move 后选择: 右值引用\n"
        "只做类型转换后原值仍是: Athena\n");
}

TEST(RaiiContentTest, DistinguishesCopyMoveConstructionAndMoveAssignment) {
    EXPECT_EQ(
        run_experiment(&RAII::move_semantics),
        "拷贝构造创建独立存储: 是\n"
        "std::move 本身搬运存储: 否\n"
        "移动构造转移原存储: 是\n"
        "移动赋值转移拷贝对象的存储: 是\n"
        "统计: 拷贝构造 1，移动构造 1，移动赋值 1\n"
        "被移动对象重新赋值后元素数: 3\n");
}

} // namespace
