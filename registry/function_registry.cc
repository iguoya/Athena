#include "function_registry.h"

#include <stdexcept>
#include <utility>

void FunctionRegistry::add(string id, RegisteredFunction function) {
    if (id.empty() || !function) {
        throw invalid_argument("Function id and callable are required");
    }
    if (!m_functions.emplace(std::move(id), std::move(function)).second) {
        throw invalid_argument("Duplicate function id");
    }
}

bool FunctionRegistry::contains(const string& id) const {
    return m_functions.contains(id);
}

void FunctionRegistry::run(const string& id, ostream& output) const {
    const auto found = m_functions.find(id);
    if (found == m_functions.end()) {
        throw out_of_range("Unknown function id: " + id);
    }
    found->second(output);
}

vector<string> FunctionRegistry::ids() const {
    vector<string> result;
    result.reserve(m_functions.size());
    for (const auto& [id, function] : m_functions) {
        result.push_back(id);
    }
    return result;
}
