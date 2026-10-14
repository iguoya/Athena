"""符号引擎的不变量测试（ADR 0025、0001）。

引擎只回答 equal / different / unknown 三种。最要紧的一条：**判不出来不等于用户错了**，
`unknown` 不许折叠成 `different`——否则学习者写对了、只是 SymPy 没化开，会被当场判错。
用 engine/.venv 里的 Python 跑：  engine/.venv/bin/python -m unittest discover -s engine
"""

from __future__ import annotations

import importlib.util
import time
import unittest
from pathlib import Path

_spec = importlib.util.spec_from_file_location("engine", Path(__file__).with_name("engine.py"))
engine = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(engine)


def verdict(a: str, b: str) -> str:
    result = engine._handle({"op": "equiv", "a": a, "b": b})
    return result["verdict"] if result.get("ok") else "error"


class EquivalenceTests(unittest.TestCase):
    def test_恒等变形判相等(self):
        for a, b in [
            ("(x+1)**2", "x**2+2*x+1"),
            ("sin(x)**2+cos(x)**2", "1"),
            ("(x**2-1)/(x-1)", "x+1"),
        ]:
            self.assertEqual(verdict(a, b), "equal", f"{a} ~ {b}")

    def test_明确不等才判不等(self):
        self.assertEqual(verdict("x", "x+1"), "different")
        self.assertEqual(verdict("2", "3"), "different")

    def test_化不开的不能判成不等(self):
        # 这两对在正数上处处相等，但对负数不等价：SymPy 在无假设下化不到 0。
        # 引擎只在正数点上采样，所以只能说「数值吻合但没证明」——绝不能是 different。
        for a, b in [("log(x**2)", "2*log(x)"), ("sqrt(x**2)", "x")]:
            self.assertEqual(verdict(a, b), "unknown", f"{a} ~ {b}")

    def test_没看懂的输入报错而不是猜(self):
        result = engine._handle({"op": "equiv", "a": "x+", "b": "x"})
        self.assertFalse(result["ok"])
        self.assertIn("左边没看懂", result["error"])
        result = engine._handle({"op": "equiv", "a": "x", "b": "2*"})
        self.assertIn("右边没看懂", result["error"])

    def test_未知操作报错(self):
        self.assertFalse(engine._handle({"op": "solve"})["ok"])


class TimeoutTests(unittest.TestCase):
    def test_超时返回unknown不拖死界面(self):
        original = engine._equiv
        engine._equiv = lambda a, b: [time.sleep(0.01) for _ in iter(int, 1)]  # 纯 Python 死循环
        previous, engine.EQUIV_TIMEOUT_S = engine.EQUIV_TIMEOUT_S, 0.3
        try:
            started = time.perf_counter()
            result = engine._handle({"op": "equiv", "a": "x", "b": "x"})
            elapsed = time.perf_counter() - started
        finally:
            engine._equiv, engine.EQUIV_TIMEOUT_S = original, previous
        self.assertEqual(result["verdict"], "unknown")
        self.assertIn("没判出来", result["note"])
        self.assertLess(elapsed, 3.0)


if __name__ == "__main__":
    unittest.main()
