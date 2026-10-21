"""scripts/archive_check.py：历史归档章节校验器的行为（ADR 0176）。"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import archive_check  # noqa: E402


def make_app(root: Path, notes, run="cli", sources=("main.cpp",), extra_case=False) -> Path:
    app = root / "app"
    case = app / "content" / "cases" / "arc_demo"
    case.mkdir(parents=True)
    (case / "main.cpp").write_text("int main(){}\nint x;\n", encoding="utf-8")
    if extra_case:
        (app / "content" / "cases" / "arc_orphan").mkdir()
    (app / "content" / "curriculum.json").write_text(
        json.dumps({"chapters": [{"id": "c", "topics": [{"id": "x.main"}]}]}), encoding="utf-8")
    block = {"type": "archive", "case": "arc_demo", "sources": list(sources), "run": run,
             "origin": {"repo": "R", "path": "P"}, "notes": notes}
    arc = {"chapters": [{"id": "archive", "layer": "archive",
                         "topics": [{"id": "x.arc.demo", "requires": ["x.main"], "lesson": {"blocks": [block]}}]}]}
    (app / "content" / "archive.json").write_text(json.dumps(arc), encoding="utf-8")
    return app


GOOD = [{"file": "main.cpp", "line": 1, "kind": "style", "text": "main 里什么都没做，也没有返回值说明。"}]


class ArchiveCheck(unittest.TestCase):
    def check(self, **kw):
        with tempfile.TemporaryDirectory() as d:
            return archive_check.check_app(make_app(Path(d), **kw))

    def test_合法条目无问题(self):
        self.assertEqual(self.check(notes=GOOD), [])

    def test_批注行号越界被拦(self):
        bad = [dict(GOOD[0], line=99)]
        self.assertTrue(any("越界" in p for p in self.check(notes=bad)))

    def test_没有批注被拦(self):
        self.assertTrue(any("没有批注" in p for p in self.check(notes=[])))

    def test_可运行却无源文件清单被拦(self):
        self.assertTrue(any("sources" in p for p in self.check(notes=GOOD, sources=())))

    def test_批注太短与未知类别被拦(self):
        bad = [dict(GOOD[0], text="太短", kind="whatever")]
        probs = self.check(notes=bad)
        self.assertTrue(any("太短" in p for p in probs) and any("kind" in p for p in probs))

    def test_孤儿案例目录被拦(self):
        self.assertTrue(any("孤儿" in p for p in self.check(notes=GOOD, extra_case=True)))


if __name__ == "__main__":
    unittest.main()
