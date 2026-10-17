"""实体展开出来的尖括号不能被当标签剥掉（sync 快照与 PO 指纹两侧同口径）。

运行：python -m unittest guide/gtkmm/scripts/test_angle_entities.py（在仓库根）或在本目录
    python -m unittest test_angle_entities
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_po import po_to_plain, snapshot_plain  # noqa: E402
from inline_md import expand_entities, inline_md, restore_angles  # noqa: E402


def md(raw: str) -> str:
    return restore_angles(inline_md(expand_entities(raw, keep_angle=True)))


class AngleEntities(unittest.TestCase):
    def test_template_args_survive(self):
        raw = "<para>Use <classname>sigc::slot&lt;R(Args...)&gt;</classname> here.</para>"
        self.assertEqual(md(raw).replace("<para>", "").replace("</para>", ""), "Use `sigc::slot<R(Args...)>` here.")

    def test_markup_text_survives_but_real_tags_go(self):
        raw = "text &lt;b&gt;bold text&lt;/b&gt; and <emphasis>real</emphasis>"
        self.assertEqual(md(raw), "text <b>bold text</b> and *real*")

    def test_po_and_snapshot_agree(self):
        raw = "Use <classname>sigc::slot&lt;R(Args...)&gt;</classname>"
        self.assertEqual(po_to_plain(raw), snapshot_plain(md(raw)))
        self.assertIn("<R(Args...)>", po_to_plain(raw))

    def test_numeric_character_references(self):
        self.assertEqual(expand_entities("copyright &#169; and Gr&#252;&#223;, &#xA9;"), "copyright © and Grüß, ©")

    def test_nested_custom_entities(self):
        custom = {"base_html": "https://x/", "base_cls": "&base_html;classGtk_1_1"}
        self.assertEqual(expand_entities("&base_cls;Button.html", custom), "https://x/classGtk_1_1Button.html")

    def test_default_expansion_unchanged(self):
        self.assertEqual(expand_entities("a &lt; b &amp; c"), "a < b & c")


if __name__ == "__main__":
    unittest.main()
