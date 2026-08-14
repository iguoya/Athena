#pragma once

#include <functional>
#include <iosfwd>
#include <map>
#include <string>
#include <vector>

using namespace std;

using RegisteredFunction = function<void(ostream&)>;

string make_function_id(
    const string& category,
    const string& chapter,
    const string& subchapter);

class FunctionRegistry {
public:
    void add(string id, RegisteredFunction function);
    bool contains(const string& id) const;
    void run(const string& id, ostream& output) const;
    vector<string> ids() const;

private:
    map<string, RegisteredFunction> m_functions;
};

FunctionRegistry create_default_function_registry();
