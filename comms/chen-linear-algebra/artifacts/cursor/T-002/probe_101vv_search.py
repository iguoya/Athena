"""POST-search 101vv book libraries for the Chen LA title / ISBN."""
import urllib.request
import urllib.parse
import ssl
import os
import re

out = os.path.dirname(os.path.abspath(__file__))
ctx = ssl.create_default_context()
endpoint = "https://www.101vv.com/index/index/search.html"
queries = [
    ("isbn", "9787560634623"),
    ("title", "实用大众线性代数"),
    ("filename", "13652907"),
]
lines = []
for qname, keyword in queries:
    for field in ("1", "2", "3", "4"):
        data = urllib.parse.urlencode(
            {"keyword": keyword, "field": field}
        ).encode("utf-8")
        dest = os.path.join(out, f"101vv_{qname}_f{field}.html")
        try:
            req = urllib.request.Request(
                endpoint,
                data=data,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Athena-T002",
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Referer": "https://www.101vv.com/",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30, context=ctx) as r:
                body = r.read()
            with open(dest, "wb") as f:
                f.write(body)
            text = body.decode("utf-8", errors="ignore")
            hits = len(re.findall(r"实用大众|13652907|9787560634623|陈怀琛", text))
            has_li = text.count("<li ")
            lines.append(
                f"OK q={qname} field={field} size={len(body)} keyword_hits={hits} li_count={has_li}"
            )
        except Exception as e:
            lines.append(
                f"FAIL q={qname} field={field} err={type(e).__name__}: {e}"
            )

text = "\n".join(lines) + "\n"
open(os.path.join(out, "probe-101vv.txt"), "w", encoding="utf-8").write(text)
print(text)