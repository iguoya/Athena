#include <iostream>
#include <string>
using namespace std;

// 基类
class Person
{
public:
    Person()
    {
        cout << "I am Born ~~~~~" << endl;
    }
    Person(double h, double w) : height(h), weight(w)
    {
        cout << "I have height and weight ~~" << endl;
    };
    void setHeight(double h)
    {
        height = h;
    }
    void setWeight(double w)
    {
        weight = w;
    }
    void say()
    {
        cout << "Greeting from China !" << endl;
    }

protected:
    double height;
    double weight;
};

// 派生类
class Male : public Person
{
private:
    string testicle;

public:
    Male() : Person(){};
    Male(double h, double w) : Person(h, w){};
    void fightBattle()
    {
        cout << "my hight is " << height << endl;
        cout << "my weight is " << weight << endl;

        cout << "I have testicle with " << testicle << " and ";
        cout << "I fight a battle" << endl;
    }
    void setTesticle(string s)
    {
        testicle = s;
    }
};

class Female : public Person
{
private:
    string vagina;

public:
    Female(double h, double w) : Person(h, w){};
    void pregnant()
    {
        cout << "my hight is " << height << endl;
        cout << "my weight is " << weight << endl;
        cout << "I have a vagina with " << vagina << " and ";
        cout << "I give a birth to a baby" << endl;
    }
    void setVagina(string s)
    {
        vagina = s;
    }
};

int main(void)
{
    Person lion(175, 60.5);
    lion.say();

    Male alexander;
    alexander.setHeight(160);
    alexander.setWeight(50);
    alexander.setTesticle("Large");
    alexander.fightBattle();

    Female catherine(165, 45);
    catherine.setVagina("Beauty");
    catherine.pregnant();

    return 0;
}