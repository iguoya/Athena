# Athena · 驾考学习（独立应用）

与其他学习应用**平级**的独立应用。技术栈：Flutter 桌面。不启动别的应用也可以
完成科目一、科目四的练习和模拟考。决策见 [`docs/decisions/`](docs/decisions/)。

## 做什么

只练中国机动车理论考的两门：

1. **科目一** 道路交通安全法律、法规和相关知识
2. **科目四** 安全文明驾驶常识（单独一卷、单独记分，跟路考不是同一张成绩）

题目都指到法条或国家标准，不用商业题库原题。标志在界面里自绘。

## 运行

需要 Flutter SDK（stable）。

```sh
cd apps/driver
launcher open driver
```

环境变量 `ATHENA_DRIVER_ROOT` 指向应用根目录（含 `content/`）。不要打开打包副本。

```sh
python3 scripts/check.py
```
