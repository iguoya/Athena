import re
import sys

sys.path.insert(0, "scripts")
from extract_source import strip_inline_md  # noqa: E402

t = "See [Wikipedia C++](https://x.org): intro."
BS = chr(92)
pattern = (
    BS + "[([^" + BS + "]]*)" + BS + "]"
    + "(" + BS + "[^)]*" + BS + ")"
)
print("pattern:", repr(pattern))
print("re.sub : ", repr(re.sub(pattern, BS + "1", t)))
print("func   : ", repr(strip_inline_md(t)))
