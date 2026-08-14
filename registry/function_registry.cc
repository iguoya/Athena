#include "function_registry.h"

#include "raii/raii.hpp"
#include "references/reference.hpp"

#include <memory>
#include <stdexcept>
#include <utility>

string make_function_id(
    const string& category,
    const string& chapter,
    const string& subchapter) {
    return category + "." + chapter + "." + subchapter;
}

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

FunctionRegistry create_default_function_registry() {
    FunctionRegistry registry;
    auto reference = make_shared<Reference>();
    registry.add("cpp.Reference.reference_basics", [reference](ostream& output) {
        reference->reference_basics(output);
    });
    registry.add("cpp.Reference.const_reference", [reference](ostream& output) {
        reference->const_reference(output);
    });
    registry.add("cpp.Reference.pass_by_reference", [reference](ostream& output) {
        reference->pass_by_reference(output);
    });
    registry.add("cpp.Reference.return_by_reference", [reference](ostream& output) {
        reference->return_by_reference(output);
    });

    auto raii = make_shared<athena::cpp::RAII>();
    registry.add("cpp.RAII.basic", [raii](ostream& output) {
        raii->basic(output);
    });
    registry.add("cpp.RAII.unique", [raii](ostream& output) {
        raii->unique(output);
    });
    registry.add("cpp.RAII.shared", [raii](ostream& output) {
        raii->shared(output);
    });
    registry.add("cpp.RAII.weak", [raii](ostream& output) {
        raii->weak(output);
    });
    registry.add("cpp.RAII.rvalue", [raii](ostream& output) {
        raii->rvalue(output);
    });
    registry.add("cpp.RAII.move_", [raii](ostream& output) {
        raii->move_(output);
    });
    return registry;
}
