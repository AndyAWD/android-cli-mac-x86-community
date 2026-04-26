"""Convert uiautomator dump XML to a JSON-friendly dict tree."""
from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any


def _attrs_to_dict(elem: ET.Element) -> dict[str, Any]:
    return {k: v for k, v in elem.attrib.items()}


def xml_to_tree(xml_text: str) -> dict[str, Any]:
    """Parse uiautomator XML into a recursive {tag, attrs, children} dict."""
    root = ET.fromstring(xml_text)
    return _to_dict(root)


def _to_dict(elem: ET.Element) -> dict[str, Any]:
    return {
        "tag": elem.tag,
        "attrs": _attrs_to_dict(elem),
        "children": [_to_dict(child) for child in list(elem)],
    }


def _flatten(node: dict[str, Any], path: str = "") -> dict[str, dict[str, Any]]:
    """Index every node by an attribute-derived stable key for diffing."""
    attrs = node.get("attrs", {})
    key = attrs.get("resource-id") or attrs.get("content-desc") or ""
    bounds = attrs.get("bounds", "")
    cls = attrs.get("class", "")
    here = f"{path}/{cls}[{bounds}]" + (f"#{key}" if key else "")
    out = {here: node}
    for child in node.get("children", []):
        out.update(_flatten(child, here))
    return out


def diff_trees(prev_xml: str, curr_xml: str) -> list[dict[str, Any]]:
    """Return flat list of changed nodes (added / removed / modified)."""
    prev_index = _flatten(xml_to_tree(prev_xml)) if prev_xml else {}
    curr_index = _flatten(xml_to_tree(curr_xml))
    changes: list[dict[str, Any]] = []
    for key in sorted(set(prev_index) | set(curr_index)):
        if key not in prev_index:
            changes.append({"change": "added", "key": key,
                            "attrs": curr_index[key]["attrs"]})
        elif key not in curr_index:
            changes.append({"change": "removed", "key": key,
                            "attrs": prev_index[key]["attrs"]})
        elif prev_index[key]["attrs"] != curr_index[key]["attrs"]:
            changes.append({
                "change": "modified",
                "key": key,
                "before": prev_index[key]["attrs"],
                "after": curr_index[key]["attrs"],
            })
    return changes
