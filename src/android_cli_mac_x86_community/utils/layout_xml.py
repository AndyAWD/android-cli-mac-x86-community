"""Convert uiautomator dump XML to a JSON-friendly dict tree."""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import Any, Union


_BOUNDS_RE = re.compile(r"\[(-?\d+),(-?\d+)\]\[(-?\d+),(-?\d+)\]")


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


def parse_bounds(value: str) -> dict[str, int] | None:
    """Parse uiautomator bounds string '[x1,y1][x2,y2]' into a dict.

    Returns {x1,y1,x2,y2,cx,cy} where cx/cy are the centre point. Returns
    None when the input does not match the expected format.
    """
    m = _BOUNDS_RE.fullmatch(value or "")
    if not m:
        return None
    x1, y1, x2, y2 = (int(v) for v in m.groups())
    return {
        "x1": x1, "y1": y1, "x2": x2, "y2": y2,
        "cx": (x1 + x2) // 2,
        "cy": (y1 + y2) // 2,
    }


def find_nodes(
    source: Union[str, dict[str, Any]],
    *,
    text: str | None = None,
    resource_id: str | None = None,
    content_desc: str | None = None,
    class_name: str | None = None,
) -> list[dict[str, Any]]:
    """Walk a layout tree and return nodes whose attrs match every given selector.

    `source` is either a parsed tree (from xml_to_tree) or raw XML text. All
    selectors are exact string equality and combined with logical AND. At
    least one selector must be provided.
    """
    if all(s is None for s in (text, resource_id, content_desc, class_name)):
        raise ValueError("at least one selector is required")

    tree = source if isinstance(source, dict) else xml_to_tree(source)
    matches: list[dict[str, Any]] = []

    def matches_attrs(attrs: dict[str, Any]) -> bool:
        return (
            (text is None or attrs.get("text") == text)
            and (resource_id is None or attrs.get("resource-id") == resource_id)
            and (content_desc is None or attrs.get("content-desc") == content_desc)
            and (class_name is None or attrs.get("class") == class_name)
        )

    def walk(node: dict[str, Any]) -> None:
        if matches_attrs(node.get("attrs", {})):
            matches.append(node)
        for child in node.get("children", []):
            walk(child)

    walk(tree)
    return matches


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
