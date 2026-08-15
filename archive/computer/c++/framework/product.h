#ifndef CHAPTER_H
#define CHAPTER_H
#include <sigc++/sigc++.h>
#include <string>
#include <iostream>
#include <sstream>
#include <iterator>
#include <memory>
#include "factory.h"
//#include <boost/format.hpp>

using namespace std;

class Product {
public:
    Product();
    virtual ~Product();
    virtual void run() = 0;

    sigc::signal<void(const string &)> display;
    sigc::signal<void(const vector<string> &)> displays;

    sigc::signal<void(vector<string> columns, vector<vector<string> > result)> displayTable;

    template<typename ... Args>
    static string format(const string& format, Args ... args)
    {
        auto size_buf = snprintf(nullptr, 0, format.c_str(), args ...) + 1;
        unique_ptr<char[]> buf(new(nothrow) char[size_buf]);

        if (!buf)
            return string("");

        snprintf(buf.get(), size_buf, format.c_str(), args ...);
        return string(buf.get(), buf.get() + size_buf - 1);
    }

    // str: 要分割的字符串
    // tokens: 保存分割结果的字符串数组
    void split(const std::string& str,
               std::vector<std::string>& tokens) {
        tokens.clear();

        std::istringstream iss(str);
        std::copy(std::istream_iterator<std::string>(iss),
                  std::istream_iterator<std::string>(),
                  std::back_inserter(tokens));
    }

    //  sigc::signal<void(const vector<string> &)> set_columns;
    //  sigc::signal<void(const vector<vector<string>> &)> display_table;
};

#endif // CHAPTER_H
