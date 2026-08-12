#include <iostream>
using namespace std;

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

int main() {
    int x = 5, y = 10;

    swapByValue(x, y);
    cout << "值传递后:  x=" << x << ", y=" << y << "  (未改变)" << endl;

    swapByRef(x, y);
    cout << "引用传递后: x=" << x << ", y=" << y << "  (已交换)" << endl;

    return 0;
}
