# ch4–ch6 判分题盲面/底面抽取（复用 ch1–ch3 那轮的方法）
# 盲面：块 id、题干、选项（无 correct/value/solution/explain/varies）
# 底面：全部字段。example/pitfall 另出一份全文供复算。
import json, glob, io

OUT = r"C:\Users\tiger\Athena\comms\self-study\artifacts\zcode\.work"
files = sorted(glob.glob(r"C:\Users\tiger\Athena\self-study\advanced-mathematics\content\sections\ch[456]-*.json"))

blind, base, ep = [], [], []
n_ret = n_num = n_cho = 0
for f in files:
    d = json.load(open(f, encoding="utf-8"))
    blind.append(f"\n# {d['id']}")
    base.append(f"\n# {d['id']}")
    for b in d["blocks"]:
        if b["kind"] == "retrieval":
            n_ret += 1
            blind.append(f"\n[{b['id']}] {b['prompt']}")
            for i, o in enumerate(b["options"]):
                blind.append(f"  {'ABCD'[i]}. {o}")
            base.append(f"\n[{b['id']}] {b['prompt']}")
            for i, o in enumerate(b["options"]):
                base.append(f"  {'ABCD'[i]}. {o}")
            base.append(f"  correct={'ABCD'[b['correct']]}")
            base.append(f"  explain: {b['explain']}")
        elif b["kind"] == "exercise":
            a = b["answer"]
            if a["type"] == "numeric":
                n_num += 1
            else:
                n_cho += 1
            blind.append(f"\n[{b['id']}] ({a['type']}) {b['stem']}")
            base.append(f"\n[{b['id']}] ({a['type']}) {b['stem']}")
            if "options" in a:
                for i, o in enumerate(a["options"]):
                    blind.append(f"  {'ABCD'[i]}. {o}")
                    base.append(f"  {'ABCD'[i]}. {o}")
                base.append(f"  correct={'ABCD'[a['correct']]}")
            else:
                base.append(f"  value={a['value']!r}")
            base.append(f"  solution: {b['solution']}")
            base.append(f"  varies: {b.get('varies','')}")
        elif b["kind"] in ("example", "pitfall", "figure"):
            ep.append(f"\n# {d['id']} / {b['kind']}\n" + json.dumps(b, ensure_ascii=False, indent=1))

open(f"{OUT}\\blind-ch46.md", "w", encoding="utf-8").write("".join(blind))
open(f"{OUT}\\base-ch46.md", "w", encoding="utf-8").write("".join(base))
open(f"{OUT}\\examples-pitfalls-ch46.md", "w", encoding="utf-8").write("".join(ep))
print(f"retrieval={n_ret} numeric={n_num} choice={n_cho} 判分题合计={n_ret+n_num+n_cho}")
