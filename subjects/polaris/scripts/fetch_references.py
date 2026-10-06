#!/usr/bin/env python3
"""下载路线图原料到 `content/sources/reference/roadmaps/`，并写 MANIFEST.json。

只拷贝**许可证允许再分发**的仓库（MIT、CC0），连同 LICENSE 一起入库；保留版权或带
相同方式共享义务的（roadmap.sh、CC BY-SA 4.0 的学习计划等）只记录链接与不拷贝的理由，
内容仅在这里用作对照，不进入应用，也不复制其文字。固定到 commit，重跑得到同一份。

用法：python scripts/fetch_references.py        （需要已登录的 gh）
"""

from __future__ import annotations

import datetime
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "content" / "sources" / "reference" / "roadmaps"

# id → 仓库、要拷贝的文件。只取说明与许可证，不取讲义和图片。
COPIED = [
    {"id": "ossu-computer-science", "repo": "ossu/computer-science",
     "files": ["README.md", "CURRICULAR_GUIDELINES.md", "LICENSE"],
     "role": "计算机科学自学课程表：按课程组织的完整学位路径，计算机一侧的对照基准"},
    {"id": "open-source-cs", "repo": "ForrestKnight/open-source-cs",
     "files": ["README.md", "LICENSE"],
     "role": "按学科方向（含体系结构、操作系统、嵌入式相关）分组的免费课程与书目"},
    {"id": "awesome-electronics", "repo": "kitspace/awesome-electronics",
     "files": ["README.md", "LICENSE"],
     "role": "电子工程资源清单：目前 GitHub 上 star 最高的电子类整理，不是路线图，只作资源对照"},
    {"id": "ai-hardware-engineer-roadmap", "repo": "ai-hpc/ai-hardware-engineer-roadmap",
     "files": ["README.md", "LICENSE"], "outline": True,
     "role": "软硬结合路线图：数字设计与 HDL → 体系结构 → 嵌入式 → FPGA / Jetson / 推理优化 → 专题方向"},
]

# 不拷贝：许可证不允许，或带共享义务。只记链接，应用内容里用来源目录引用。
LINKED_ONLY = [
    {"id": "roadmap-sh", "repo": "nilbuild/developer-roadmap", "url": "https://github.com/kamranahmedse/developer-roadmap",
     "reason": "保留全部版权，仅限个人使用，不得以任何形式在别处发布其内容，只允许分享链接。仅作对照，不拷贝。",
     "role": "star 最高的开发者路线图（约 36.9 万）；硬件相关只有「计算机如何工作、缓存、中断」几项，没有软硬结合与电子路线"},
    {"id": "coding-interview-university", "repo": "jwasham/coding-interview-university",
     "reason": "CC BY-SA 4.0：拷贝或改编的内容须同协议共享，会让本应用的内容被动成为衍生作品。只引用链接。",
     "role": "star 第二高（约 36.2 万）的计算机学习计划，面向面试，数据结构与算法为主"},
    {"id": "teachyourselfcs-cn", "repo": "izackwu/TeachYourselfCS-CN",
     "reason": "CC BY-SA 4.0，理由同上。只引用链接。",
     "role": "「Teach Yourself Computer Science」中文版（约 2.2 万）：九个必修领域，含计算机体系结构"},
    {"id": "awesome-hdl", "repo": "drom/awesome-hdl", "reason": "仓库未声明许可证，默认保留版权。只引用链接。",
     "role": "硬件描述语言资源清单（约 1.2 千）"},
    {"id": "awesome-embedded-systems", "repo": "embedded-boston/awesome-embedded-systems",
     "reason": "仓库未声明许可证，默认保留版权。只引用链接。", "role": "嵌入式资源清单（约 1 千）"},
    {"id": "awesome-fpga", "repo": "Vitorian/awesome-fpga", "reason": "GPL-3.0，且 2017 年后无更新。只引用链接。",
     "role": "FPGA 资源清单（约 400），已停更"},
]


def gh(*args: str) -> bytes:
    completed = subprocess.run(["gh", *args], capture_output=True)
    if completed.returncode:
        raise SystemExit(f"gh {' '.join(args)} 失败：{completed.stderr.decode('utf-8', 'replace')}")
    return completed.stdout


def repo_meta(repo: str) -> dict:
    info = json.loads(gh("repo", "view", repo, "--json", "stargazerCount,licenseInfo,url"))
    sha = gh("api", f"repos/{repo}/commits/HEAD", "--jq", ".sha").decode().strip()
    return {"stars": info["stargazerCount"], "license": (info.get("licenseInfo") or {}).get("key"),
            "url": info["url"], "commit": sha}


def outline(repo: str, sha: str) -> str:
    """目录大纲：只取目录路径（深度 ≤ 3），不含图片与讲义。派生自仓库目录树，非原文。"""
    tree = gh("api", f"repos/{repo}/git/trees/{sha}?recursive=1", "--jq",
              '.tree[] | select(.type=="tree") | .path').decode("utf-8").splitlines()
    kept = [p for p in tree if not p.startswith(("Assets", ".github")) and p.count("/") <= 2]
    return "\n".join(kept) + "\n"


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")
    manifest = {"retrieved": datetime.date.today().isoformat(), "tool": "scripts/fetch_references.py",
                "copied": [], "linked_only": []}

    for spec in COPIED:
        meta = repo_meta(spec["repo"])
        if meta["license"] not in ("mit", "cc0-1.0"):
            raise SystemExit(f"{spec['repo']} 的许可证是 {meta['license']}，不是 MIT / CC0，不能拷贝入库")
        directory = TARGET / spec["id"]
        directory.mkdir(parents=True, exist_ok=True)
        files = []
        for path in spec["files"]:
            data = gh("api", "-H", "Accept: application/vnd.github.raw",
                      f"repos/{spec['repo']}/contents/{path}?ref={meta['commit']}")
            (directory / path).write_bytes(data)
            files.append({"path": path, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
        if spec.get("outline"):
            text = outline(spec["repo"], meta["commit"]).encode("utf-8")
            (directory / "OUTLINE.txt").write_bytes(text)
            files.append({"path": "OUTLINE.txt", "bytes": len(text), "sha256": hashlib.sha256(text).hexdigest(),
                          "derived": "由仓库目录树生成，深度 ≤ 3，不含 Assets 与 .github"})
        manifest["copied"].append({"id": spec["id"], "repo": spec["repo"], "role": spec["role"], **meta, "files": files})
        print(f"已取 {spec['repo']}（{meta['stars']} star，{meta['license']}，{meta['commit'][:8]}）：{len(files)} 个文件")

    for spec in LINKED_ONLY:
        meta = repo_meta(spec["repo"])
        manifest["linked_only"].append({**spec, "stars": meta["stars"], "license": meta["license"],
                                        "commit": meta["commit"]})
        print(f"仅引用 {spec['repo']}（{meta['stars']} star，{meta['license']}）")

    TARGET.mkdir(parents=True, exist_ok=True)
    (TARGET / "MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
