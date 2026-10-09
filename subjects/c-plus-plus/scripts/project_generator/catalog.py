"""Render the trusted, normalized runtime chapter catalog."""

import json


def render_catalog(model: dict) -> str:
    payload = {
        "generated_notice": (
            "Generated from resources/athena.json by generate_project.py. "
            "DO NOT EDIT."
        ),
        **model["runtime_catalog"],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
