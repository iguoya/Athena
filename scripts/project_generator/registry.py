"""Render FunctionRegistry bindings from the validated project model."""


def render_registry(bindings: list[dict]) -> str:
    headers = sorted({binding["header"] for binding in bindings})
    lines = [
        "// Generated from resources/athena.json by generate_project.py. DO NOT EDIT.",
        '#include "registry/function_registry.h"',
        "",
    ]
    lines.extend(f'#include "{header}"' for header in headers)
    lines.extend(["", "#include <memory>", "", "using namespace std;", ""])
    lines.extend(
        [
            "FunctionRegistry create_default_function_registry() {",
            "    FunctionRegistry registry;",
        ]
    )
    for binding in bindings:
        category = binding["category"]
        chapter = binding["chapter"]
        variable = f"{category}_{chapter}".lower()
        class_name = f"athena::{category}::{chapter}"
        lines.append(f"    auto {variable} = make_shared<{class_name}>();")
        for method in binding["methods"]:
            lines.append(
                f'    registry.add(make_function_id("{category}", "{chapter}", "{method}"), '
                f"[{variable}](ostream& output) {{"
            )
            lines.append(f"        {variable}->{method}(output);")
            lines.append("    });")
        lines.append("")
    lines.extend(["    return registry;", "}", ""])
    return "\n".join(lines)
