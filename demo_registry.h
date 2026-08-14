#pragma once

#include <functional>
#include <iosfwd>
#include <map>
#include <string>
#include <vector>

using namespace std;

using DemoFunction = function<void(ostream&)>;

string make_demo_id(
    const string& category,
    const string& chapter,
    const string& subchapter);

class DemoRegistry {
public:
    void add(string id, DemoFunction function);
    bool contains(const string& id) const;
    void run(const string& id, ostream& output) const;
    vector<string> ids() const;

private:
    map<string, DemoFunction> m_functions;
};

DemoRegistry create_default_demo_registry();
