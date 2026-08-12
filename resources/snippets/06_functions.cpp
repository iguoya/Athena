// 值传递 vs 引用传递 演示
class Demo {
public:
    void run() {
        int x = 5, y = 10;

        swapByValue(x, y);
        cout << "值传递后:  x=" << x << ", y=" << y << "  (未改变)" << endl;

        swapByRef(x, y);
        cout << "引用传递后: x=" << x << ", y=" << y << "  (已交换)" << endl;
    }

private:
    void swapByValue(int a, int b) {
        int temp = a;
        a = b;
        b = temp;
    }

    void swapByRef(int &a, int &b) {
        int temp = a;
        a = b;
        b = temp;
    }
};
