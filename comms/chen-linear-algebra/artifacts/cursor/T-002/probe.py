import urllib.request
import ssl
import os

out = os.path.dirname(os.path.abspath(__file__))
os.makedirs(out, exist_ok=True)
log_path = os.path.join(out, "probe-python.txt")
ctx = ssl.create_default_context()
urls = [
    ("csdn_bbs", "https://bbs.csdn.net/topics/396870384"),
    ("duodown", "https://www.duodown.com/material/340411796.html"),
    ("101vv", "https://www.101vv.com/"),
    ("101vv_search", "https://www.101vv.com/?s=9787560634623"),
    (
        "libgen",
        "https://libgen.is/search.php?req=9787560634623&lg_topic=libgen&open=0&view=simple&res=25&phrase=1&column=identifier",
    ),
    ("annas", "https://annas-archive.org/search?q=9787560634623"),
    ("zlib", "https://z-library.sk/s/9787560634623"),
    ("sohu_probe", "https://pdf.windowsfront.com/jd_11558945.pdf"),
]
lines = []
for name, url in urls:
    dest = os.path.join(out, name + ".bin")
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Athena-T002"
            },
        )
        with urllib.request.urlopen(req, timeout=25, context=ctx) as r:
            data = r.read(2_000_000)
            ct = r.headers.get("Content-Type", "")
            code = r.status
        with open(dest, "wb") as f:
            f.write(data)
        magic = data[:5]
        lines.append(
            f"OK {name} status={code} ct={ct} size={len(data)} magic={magic!r} url={url}"
        )
    except Exception as e:
        lines.append(f"FAIL {name} err={type(e).__name__}: {e} url={url}")

text = "\n".join(lines) + "\n"
open(log_path, "w", encoding="utf-8").write(text)
print(text)