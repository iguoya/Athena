#ifndef KEYWORD_H
#define KEYWORD_H
#include "product.h"

typedef struct {
    size_t id;
    string name;
    string input;
    string result;
} Row;

class Keyword : public Product
{
public:
    Keyword();
    void run() override;
};
REGISTERCLASS(Keyword);
#endif // KEYWORD_H
