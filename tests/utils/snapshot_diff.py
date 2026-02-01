import json
from typing import Any, Dict, List, Tuple


def diff_json(expected: Any, actual: Any, path: str = "") -> Dict[str, List[str]]:
    changes = {"added": [], "removed": [], "changed": []}

    if isinstance(expected, dict) and isinstance(actual, dict):
        expected_keys = set(expected.keys())
        actual_keys = set(actual.keys())
        for key in sorted(actual_keys - expected_keys):
            changes["added"].append(_join_path(path, key))
        for key in sorted(expected_keys - actual_keys):
            changes["removed"].append(_join_path(path, key))
        for key in sorted(expected_keys & actual_keys):
            sub = diff_json(expected[key], actual[key], _join_path(path, key))
            for k in changes:
                changes[k].extend(sub[k])
        return changes

    if isinstance(expected, list) and isinstance(actual, list):
        if expected != actual:
            changes["changed"].append(path or "$")
        return changes

    if expected != actual:
        changes["changed"].append(path or "$")
    return changes


def diff_markdown_by_heading(expected_md: str, actual_md: str) -> Dict[str, List[str]]:
    expected_sections = _split_markdown_sections(expected_md)
    actual_sections = _split_markdown_sections(actual_md)

    expected_heads = set(expected_sections.keys())
    actual_heads = set(actual_sections.keys())

    added = sorted(actual_heads - expected_heads)
    removed = sorted(expected_heads - actual_heads)
    changed = []
    for head in sorted(expected_heads & actual_heads):
        if expected_sections[head] != actual_sections[head]:
            changed.append(head)

    return {"added": added, "removed": removed, "changed": changed}


def format_json_diff(changes: Dict[str, List[str]]) -> str:
    lines = ["JSON Snapshot Diff:"]
    for key in ["added", "removed", "changed"]:
        items = changes.get(key, [])
        if items:
            lines.append(f"- {key}:")
            lines.extend([f"  - {item}" for item in items])
    return "\n".join(lines)


def format_markdown_diff(changes: Dict[str, List[str]]) -> str:
    lines = ["Markdown Snapshot Diff (by heading):"]
    for key in ["added", "removed", "changed"]:
        items = changes.get(key, [])
        if items:
            lines.append(f"- {key}:")
            lines.extend([f"  - {item}" for item in items])
    return "\n".join(lines)


def load_json(path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _split_markdown_sections(md: str) -> Dict[str, str]:
    sections: Dict[str, List[str]] = {}
    current = "ROOT"
    sections[current] = []
    for line in md.splitlines():
        if line.startswith("#"):
            current = line.strip()
            sections.setdefault(current, [])
        sections[current].append(line)
    return {k: "\n".join(v).strip() for k, v in sections.items()}


def _join_path(path: str, key: str) -> str:
    return f"{path}.{key}" if path else key
