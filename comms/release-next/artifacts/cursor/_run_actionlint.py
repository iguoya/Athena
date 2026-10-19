"""把 machine job 并入 release.yml 临时副本后跑 actionlint（带仓库 .github/actionlint.yaml）。"""
from pathlib import Path
import subprocess
import sys

here = Path(__file__).resolve().parent
root = here.parents[3]  # Athena/
src = (root / ".github/workflows/release.yml").read_text(encoding="utf-8")
draft = (here / "machine-release.yml").read_text(encoding="utf-8")
if not draft.startswith("\n"):
    draft = "\n" + draft
if not draft.endswith("\n"):
    draft += "\n"
merged = src.rstrip() + "\n" + draft
old = "needs: [macos, linux, windows, driver, ascent, tauri-apps]"
new = "needs: [macos, linux, windows, driver, ascent, tauri-apps, machine]"
if old not in merged:
    print("WARN: needs pattern not found", file=sys.stderr)
else:
    merged = merged.replace(old, new, 1)

out = here / "_release-with-machine.yml"
out.write_text(merged, encoding="utf-8", newline="\n")
print(f"wrote {out} bytes={out.stat().st_size}")

config = root / ".github/actionlint.yaml"
proc = subprocess.run(
    ["actionlint", "-config-file", str(config), str(out)],
    capture_output=True,
    text=True,
)
text = (proc.stdout or "") + (proc.stderr or "")
evidence = here / "machine-actionlint.out.txt"
evidence.write_text(
    "$ python comms/release-next/artifacts/cursor/_run_actionlint.py\n"
    f"config: {config}\n"
    f"temp: {out.name}\n"
    f"exit={proc.returncode}\n"
    f"{text if text.strip() else '(no output — zero findings)'}\n",
    encoding="utf-8",
)
print(text if text.strip() else "(no output — zero findings)")
print("EXIT", proc.returncode)
sys.exit(proc.returncode)
