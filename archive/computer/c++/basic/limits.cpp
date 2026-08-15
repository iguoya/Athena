#include "limits.h"

Limits::Limits()
{

}

void Limits::run()
{

    vector<string> columns = {"数据类型", "字节长度", "最大值", "最小值"};

    vector<vector<string> > result = {
        {"bool", to_string(sizeof(bool)), "", ""},
        {"char", to_string(sizeof(char)), to_string(numeric_limits<char>::max()), to_string(numeric_limits<char>::min())},
        {"unsigned char", to_string(sizeof(unsigned char)), to_string(numeric_limits<unsigned char>::max()), to_string(numeric_limits<unsigned char>::min())},
        {"wchar_t", to_string(sizeof(wchar_t)), to_string(numeric_limits<wchar_t>::max()), to_string(numeric_limits<wchar_t>::min())},

        {"short", to_string(sizeof(short)), to_string(numeric_limits<short>::max()), to_string(numeric_limits<short>::min())},
        {"int", to_string(sizeof(int)), to_string(numeric_limits<int>::max()), to_string(numeric_limits<int>::min())},
        {"unsigned int", to_string(sizeof(unsigned int)), to_string(numeric_limits<unsigned int>::max()), to_string(numeric_limits<unsigned int>::min())},
        {"size_t", to_string(sizeof(size_t)), to_string(numeric_limits<size_t>::max()), to_string(numeric_limits<size_t>::min())},


        {"long", to_string(sizeof(long)), to_string(numeric_limits<long>::max()), to_string(numeric_limits<long>::min())},
        {"long int", to_string(sizeof(long int)), to_string(numeric_limits<long int>::max()), to_string(numeric_limits<long int>::min())},
        {"long long", to_string(sizeof(long long)), to_string(numeric_limits<long long>::max()), to_string(numeric_limits<long long>::min())},
        {"unsigned long", to_string(sizeof(unsigned long)), to_string(numeric_limits<unsigned long>::max()), to_string(numeric_limits<unsigned long>::min())},


        {"float", to_string(sizeof(float)), format("%f", numeric_limits<float>::max()), format("%f", numeric_limits<float>::min())},
        {"double", to_string(sizeof(double)), "---", "---"},
//        {"double", to_string(sizeof(double)), format("%lf", numeric_limits<double>::max()), format("%lf", numeric_limits<double>::min())},
//        //                {"long double", to_string(sizeof(long double)), to_string(numeric_limits<long double>::max()), to_string(numeric_limits<long double>::min())},

        {"string", to_string(sizeof(string)), numeric_limits<string>::max(), numeric_limits<string>::min()},






    };
    displayTable(columns, result);

    cout << "-----float-----" << endl;
    cout << "max = " << numeric_limits<float>::max() << endl;
    cout << "min = " << numeric_limits<float>::min() << endl;
    cout << "lowest = " << numeric_limits<float>::lowest() << endl;
    cout << "epsilon = " << numeric_limits<float>::epsilon() << endl;

    cout << "-----double-----" << endl;
    cout << "max = " << numeric_limits<double>::max() << endl;
    cout << "min = " << numeric_limits<double>::min() << endl;
    cout << "lowest = " << numeric_limits<double>::lowest() << endl;
    cout << "epsilon = " << numeric_limits<double>::epsilon() << endl;



    //    cout << "string: \t" << "所占字节数：" << sizeof(string) << endl;
    //    cout << "\t最大值：" <<  "\t最小值：" << (numeric_limits<string>::min)() << endl;
    //    cout << "type: \t\t" << "************size**************"<< endl;
}
