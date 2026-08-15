#include "random.h"

Random::Random()
{

}

void Random::run()
{
    std::random_device rd;

//     for (int i = 0; i < 100; i++) {
//         std::cout << rd() << std::endl;
//     }

    // std::random_device rd;
    std::mt19937 mt(rd());
    std::uniform_int_distribution<int> dist(0, 1000);
    auto dice = std::bind(dist, mt);

    vector<vector<string> > result;
    vector<string> line;
    for (int i = 1; i <= 100; i++) {
        line.emplace_back(to_string(dice()));
        if(i % 10 == 0) {
            result.emplace_back(line);
            line.clear();
        }
//        std::cout << dice() << std::endl;
    }
    vector<string> columns = {};
    displayTable(columns, result);


    result.clear();
    vector<unsigned int> sample(100, 0);
//    default_random_engine e(random_device{}());
    default_random_engine e(0);
    uniform_int_distribution<unsigned> u(1000, 10000);


    for (int i = 1; i <= 100; i++) {
        line.emplace_back(to_string(u(e)));
        if(i % 10 == 0) {
            result.emplace_back(line);
            line.clear();
        }
//        std::cout << dice() << std::endl;
    }
    displayTable(columns, result);

}
