#include "StrategyContext.h"
#include "ConcreteStrategyA.h"
#include "ConcreteStrategyB.h"
#include "QuickSort.h"
#include "BubbleSort.h"

vector<string> StrategyContext::run() {
	// TODO - implement StrategyContext::run
    vector<string> result;
    setStrategy(new ConcreteStrategyA);
    result.push_back(strategy->execute());
    setStrategy(new ConcreteStrategyB);
    result.push_back(strategy->execute());

    sort = new BubbleSort;
    result.push_back(sort->operation());

    sort = new QuickSort;
    result.push_back(sort->operation());

    return result;
}

Strategy* StrategyContext::getStrategy() {
	return this->strategy;
}

void StrategyContext::setStrategy(Strategy* strategy) {
	this->strategy = strategy;
}

SortAlgorithm* StrategyContext::getSort() {
	return this->sort;
}

void StrategyContext::setSort(SortAlgorithm* sort) {
	this->sort = sort;
}
