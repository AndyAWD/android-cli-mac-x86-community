from __future__ import annotations

from android_cli_mac_x86_community.utils.layout_xml import diff_trees, xml_to_tree


SAMPLE_XML = """<?xml version='1.0' encoding='UTF-8' standalone='yes' ?>
<hierarchy rotation="0">
  <node class="android.widget.FrameLayout" bounds="[0,0][1080,1920]">
    <node class="android.widget.TextView" resource-id="id/title"
          text="Hello" bounds="[0,0][500,100]"/>
    <node class="android.widget.Button" resource-id="id/submit"
          text="OK" bounds="[100,200][300,260]"/>
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
    assert len(frame["children"]) == 2


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
