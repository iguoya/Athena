"""符号引擎：常驻进程，一行一个 JSON（ADR 0025）。

只回答「两个表达式等不等价」，不回答「答案是什么」——工具是裁判不是计算器
（ADR 0001 第 1 节）。任何把完整解答直接送回前端的路径都需要另开 ADR。

协议（NDJSON，stdin 进 stdout 出，每行一个对象）：
    → {"id": 1, "op": "ping"}
    ← {"id": 1, "ok": true, "sympy": "1.14.0", "import_ms": 406}

    → {"id": 2, "op": "equiv", "a": "x**2-1", "b": "(x-1)*(x+1)"}
    ← {"id": 2, "ok": true, "verdict": "equal", "ms": 3.1}

verdict 三取一：equal / different / unknown。
**unknown 不许折叠成 different**：判不出来不等于用户错了，可能只是没化开。
误判会摧毁这个工具的可信度，比慢更致命（ADR 0001 第 1 节第 3 条）。
"""

import _thread
import json
import sys
import threading
import time

# import 的钱只付这一次——引擎常驻的全部理由（ADR 0001 第 2 节实测：它占冷启动的九成）
_t0 = time.perf_counter()
import sympy
from sympy.parsing.sympy_parser import parse_expr

IMPORT_MS = (time.perf_counter() - _t0) * 1000

# 光 import sympy 还不够：simplify 会在首次调用时再拉一批子模块，实测头一次
# equiv 要 365 ms 而后续只要 3–40 ms。把这笔钱在启动时付掉，别让它落在
# 用户写完第一步、最期待反馈的那一刻（ADR 0001 第 3 节：预热要掩盖掉冷启动）。
_t1 = time.perf_counter()
_x = sympy.Symbol("x")
sympy.simplify(_x**2 - 1 - (_x - 1) * (_x + 1))
WARMUP_MS = (time.perf_counter() - _t1) * 1000


# SymPy 个别调用（某些 integrate、dsolve）会跑很久。卡住比答错好一点，但也只好
# 一点——超时一律返回 unknown，界面照常往下走，不让人对着转圈等（ADR 0011：
# 消除无效挫折）。
EQUIV_TIMEOUT_S = 5.0


def _call_with_timeout(seconds, fn):
    """限时执行 fn，返回 (结果, 是否超时)。

    原来是 signal.setitimer(ITIMER_REAL) + SIGALRM。那套是 POSIX 专有的——
    Windows 上连 signal.SIGALRM 这个属性都没有，引擎在 import 阶段就
    AttributeError 崩掉，整条验算链路在那个平台上从来没起来过。

    改用定时器线程向主线程投递 KeyboardInterrupt：三个平台同一套代码，不写
    平台分支（主仓库 ADR 0047）。SymPy 是纯 Python，会在字节码边界响应中断。

    `fired` 用来区分「我们放的超时」和「使用者真的按了 Ctrl-C」——后者要原样
    抛回去，不能悄悄吞成一次 unknown。

    **已知局限**：中断在字节码边界生效，打不断 C 层的阻塞调用（`time.sleep`
    之类）。原来的 SIGALRM 在这点上更强——信号能打断系统调用。但引擎只做符号
    计算，不阻塞在系统调用上，实测覆盖了真实场景：SymPy 的难积分
    （`integrate(exp(x**3)*sin(x**2), x)`）1.51 秒准时中断，纯 Python 死循环
    0.51 秒中断。
    """
    fired = threading.Event()

    def _fire():
        fired.set()
        _thread.interrupt_main()

    timer = threading.Timer(seconds, _fire)
    timer.start()
    try:
        return fn(), False
    except KeyboardInterrupt:
        if fired.is_set():
            return None, True
        raise
    finally:
        timer.cancel()


def _parse(text):
    """解析失败要说清楚是哪个记号没认出来，不得静默猜成另一个表达式。"""
    try:
        return parse_expr(text, evaluate=False), None
    except Exception as exc:  # noqa: BLE001 — 解析层什么都可能抛
        return None, f"{type(exc).__name__}: {exc}"


def _equiv(a_text, b_text):
    a, err = _parse(a_text)
    if err:
        return {"ok": False, "error": f"左边没看懂 —— {err}"}
    b, err = _parse(b_text)
    if err:
        return {"ok": False, "error": f"右边没看懂 —— {err}"}

    # 先化简差；simplify 化不开不代表不等价，所以后面还有一道数值关
    try:
        diff = sympy.simplify(a - b)
    except Exception as exc:  # noqa: BLE001
        return {"ok": True, "verdict": "unknown", "note": f"化简失败：{type(exc).__name__}"}

    if diff == 0:
        return {"ok": True, "verdict": "equal"}

    # simplify 没化到 0，可能是真不等，也可能是它化不动。用随机数值再验一道：
    # 数值明显不同 → 确实不等；数值处处吻合而符号化不开 → 只能说 unknown。
    syms = sorted(diff.free_symbols, key=str)
    if not syms:
        try:
            val = complex(diff.evalf())
            return {"ok": True, "verdict": "equal" if abs(val) < 1e-9 else "different"}
        except Exception:  # noqa: BLE001
            return {"ok": True, "verdict": "unknown", "note": "常数项求值失败"}

    import random

    rng = random.Random(20260914)
    mismatch = 0
    evaluated = 0
    for _ in range(12):
        # 避开 0 和小整数：那里 log/除法容易恰好碰上奇点，把「未定义」误读成「不等」
        subs = {s: sympy.Rational(rng.randint(2, 97), rng.randint(2, 13)) for s in syms}
        try:
            val = complex(diff.subs(subs).evalf())
        except Exception:  # noqa: BLE001
            continue
        if val != val or abs(val) == float("inf"):  # NaN / inf：这点不能作数
            continue
        evaluated += 1
        if abs(val) > 1e-8:
            mismatch += 1

    if evaluated == 0:
        return {"ok": True, "verdict": "unknown", "note": "取不到可用的数值点"}
    if mismatch == evaluated:
        return {"ok": True, "verdict": "different"}
    if mismatch == 0:
        # 处处吻合但符号化不开：十有八九是等价的，但「十有八九」不能当判据用
        return {"ok": True, "verdict": "unknown", "note": "数值处处吻合，但没能化简证明"}
    return {"ok": True, "verdict": "unknown", "note": "数值结果不一致，可能碰上了定义域边界"}


def _handle(req):
    op = req.get("op")
    if op == "ping":
        return {
            "ok": True,
            "sympy": sympy.__version__,
            "import_ms": round(IMPORT_MS, 1),
            "warmup_ms": round(WARMUP_MS, 1),
        }
    if op == "equiv":
        result, timed_out = _call_with_timeout(
            EQUIV_TIMEOUT_S, lambda: _equiv(req.get("a", ""), req.get("b", ""))
        )
        if timed_out:
            return {
                "ok": True,
                "verdict": "unknown",
                "note": f"超过 {EQUIV_TIMEOUT_S:.0f} 秒还没判出来",
            }
        return result
    return {"ok": False, "error": f"未知操作 {op!r}"}


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError as exc:
            print(json.dumps({"id": None, "ok": False, "error": f"JSON 解析失败：{exc}"}), flush=True)
            continue

        started = time.perf_counter()
        try:
            res = _handle(req)
        except Exception as exc:  # noqa: BLE001 — 引擎不能因为一次异常就死掉
            res = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
        res["id"] = req.get("id")
        res["ms"] = round((time.perf_counter() - started) * 1000, 2)
        print(json.dumps(res, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
