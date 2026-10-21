#ifndef STRATEGYCONTEXT_H
#define STRATEGYCONTEXT_H
#include "Strategy.h"
#include "SortAlgorithm.h"
#include <vector>
class StrategyContext {

private:

public:
    Strategy* strategy;
    SortAlgorithm* sort;
    vector<string> result;

	vector<string> run();

	Strategy* getStrategy();

	void setStrategy(Strategy* strategy);

	SortAlgorithm* getSort();

	void setSort(SortAlgorithm* sort);
};

#endif
