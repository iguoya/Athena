#include "numberdigit.h"

size_t NumberDigit::typeID = qRegisterMetaType<NumberDigit*>("NumberDigit");
NumberDigit::NumberDigit()
{

}

void NumberDigit::run()
{
    digit(m_number);

    displayList(series_result);
}

size_t NumberDigit::digit(size_t number)
{
    series_result.insert(0, QString::number(number % 10));
    if(number / 10 == 0) {
        return number;
    } else {
        return digit(number / 10);
    }
}
