// 第二题：括号匹配。栈：遇左进，遇右对顶。
#include <iostream>
#include <string>
#include <vector>

using namespace std;

bool is_open(char c) { return c == '(' || c == '[' || c == '{'; }

char match_of(char c) {
    if (c == ')') return '(';
    if (c == ']') return '[';
    return '{';
}

// TODO(学员)：判断 s 是否括号匹配。可用 vector<char> 当栈。
bool valid(const string& s) {
    (void)s;
    return false; // TODO: 左括号入栈，右括号与栈顶配对
}

// —— 以下驱动请勿改 ——
int main() {
    cout << "ok1=" << (valid("()[]") ? 1 : 0) << '\n';
    cout << "ok2=" << (valid("([)]") ? 1 : 0) << '\n';
    cout << "ok3=" << (valid("{[]}") ? 1 : 0) << '\n';
    return 0;
}
