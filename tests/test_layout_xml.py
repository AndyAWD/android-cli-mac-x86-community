from __future__ import annotations

import pytest

from android_cli_mac_x86_community.utils.layout_xml import (
    diff_trees,
    find_nodes,
    parse_bounds,
    xml_to_tree,
)


SAMPLE_XML = """<?xml version='1.0' encoding='UTF-8' standalone='yes' ?>
<hierarchy rotation="0">
  <node class="android.widget.FrameLayout" bounds="[0,0][1080,1920]">
    <node class="android.widget.TextView" resource-id="id/title"
          text="Hello" content-desc="Greeting" bounds="[0,0][500,100]"/>
    <node class="android.widget.Button" resource-id="id/submit"
          text="OK" bounds="[100,200][300,260]"/>
    <node class="android.widget.Button" resource-id="id/cancel"
          text="Cancel" bounds="[400,200][600,260]"/>
  </node>
</hierarchy>
"""


MODIFIED_XML = """<?xml version='1.0' encoding='UTF-8' standalone='yes' ?>
<hierarchy rotation="0">
  <node class="android.widget.FrameLayout" bounds="[0,0][1080,1920]">
    <node class="android.widget.TextView" resource-id="id/title"
          text="Hi" bounds="[0,0][500,100]"/>
    <node class="android.widget.Button" resource-id="id/cancel"
          text="Cancel" bounds="[100,200][300,260]"/>
  </node>
</hierarchy>
"""


def test_xml_to_tree_basic_shape():
    tree = xml_to_tree(SAMPLE_XML)
    assert tree["tag"] == "hierarchy"
    assert tree["attrs"]["rotation"] == "0"
    assert len(tree["children"]) == 1
    frame = tree["children"][0]
    assert frame["attrs"]["class"] == "android.widget.FrameLayout"
    assert len(frame["children"]) == 3


def test_diff_no_previous_marks_everything_added():
    changes = diff_trees("", SAMPLE_XML)
    assert changes
    assert all(c["change"] == "added" for c in changes)


def test_diff_modified_text_attr():
    changes = diff_trees(SAMPLE_XML, MODIFIED_XML)
    kinds = {c["change"] for c in changes}
    assert "modified" in kinds or {"added", "removed"} <= kinds


def test_diff_identical_produces_no_changes():
    assert diff_trees(SAMPLE_XML, SAMPLE_XML) == []


def test_parse_bounds_returns_corners_and_centre():
    assert parse_bounds("[100,200][300,400]") == {
        "x1": 100, "y1": 200, "x2": 300, "y2": 400,
        "cx": 200, "cy": 300,
    }


def test_parse_bounds_invalid_returns_none():
    assert parse_bounds("not bounds") is None
    assert parse_bounds("") is None


def test_find_nodes_by_text():
    nodes = find_nodes(SAMPLE_XML, text="OK")
    assert len(nodes) == 1
    assert nodes[0]["attrs"]["resource-id"] == "id/submit"


def test_find_nodes_by_resource_id():
    nodes = find_nodes(SAMPLE_XML, resource_id="id/title")
    assert len(nodes) == 1
    assert nodes[0]["attrs"]["text"] == "Hello"


def test_find_nodes_by_content_desc():
    nodes = find_nodes(SAMPLE_XML, content_desc="Greeting")
    assert len(nodes) == 1
    assert nodes[0]["attrs"]["resource-id"] == "id/title"


def test_find_nodes_by_class_returns_all_matching():
    nodes = find_nodes(SAMPLE_XML, class_name="android.widget.Button")
    assert {n["attrs"]["resource-id"] for n in nodes} == {"id/submit", "id/cancel"}


def test_find_nodes_combined_selectors_use_and():
    # text=OK 但 resource-id=id/title 不匹配 → 沒結果
    assert find_nodes(SAMPLE_XML, text="OK", resource_id="id/title") == []


def test_find_nodes_no_match_returns_empty_list():
    assert find_nodes(SAMPLE_XML, text="不存在") == []


def test_find_nodes_requires_at_least_one_selector():
    with pytest.raises(ValueError):
        find_nodes(SAMPLE_XML)


def test_find_nodes_accepts_parsed_tree():
    tree = xml_to_tree(SAMPLE_XML)
    nodes = find_nodes(tree, text="OK")
    assert len(nodes) == 1
