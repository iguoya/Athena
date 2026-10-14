#!/usr/bin/env python3
"""把手册里的插图渲染成 SVG（content/figures/<图名>.svg），开发期脚本，使用者不需要。

  <有 matplotlib 的 python> scripts/render_figures.py [图名 …]

手册的图由 upstream/octave/doc/interpreter/*images.m 里的 Octave 代码画出来（plotimages.m、interpimages.m）。
本脚本分两步，**数据由真 Octave 算，图形由 matplotlib 画**：

  1. 把 *images.m 里这幅图的计算部分原样交给本机 Octave（不开图形窗口），算出要画的数组，用 jsonencode 输出；
  2. 用 matplotlib 按 *images.m 里的绘图调用（线型、颜色、标签、标题、图例位置）画成 SVG。

为什么不直接让 Octave 自己出图：云开发环境没有显示，Octave 的 gnuplot 图形后端在无显示时创建坐标轴就失败
（ft_text_renderer: invalid bounding box）。有可用图形的本机上应当改用 Octave 原生渲染，见 docs/HANDOFF.md「Octave 插图」一节：
同名 SVG 直接替换本脚本的产物即可，界面按图名读取，不需要改别处。

只渲染 scope.json 里各页 `figures` 列出的图。
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "content" / "figures"
OCTAVE = shutil.which("octave-cli") or shutil.which("octave")

# 数据部分：来自 plotimages.m / interpimages.m 的计算，原样；末尾把要画的数组打包成 struct 交给 jsonencode
DATA = {
    "plot": "x = -10:0.1:10; y = sin (x); out = struct ('x', x, 'y', y);",
    "hist": "randn ('state', 1); d = randn (10000, 1); [nn, xx] = hist (d, 30); out = struct ('n', nn, 'x', xx);",
    "polar": "t = 0:0.1:10*pi; out = struct ('t', t);",
    "mesh": ("tx = ty = linspace (-8, 8, 41)'; [xx, yy] = meshgrid (tx, ty); r = sqrt (xx .^ 2 + yy .^ 2) + eps; "
             "tz = sin (r) ./ r; out = struct ('x', tx, 'y', ty, 'z', tz);"),
    "plot3": ("t = 0:0.1:10*pi; r = linspace (0, 1, numel (t)); z = linspace (0, 1, numel (t)); "
              "out = struct ('x', r.*sin (t), 'y', r.*cos (t), 'z', z);"),
    "interpderiv1": ("t = -2:2; ti = -2:0.025:2; y = sign (t); ys = interp1 (t, y, ti, 'spline'); yp = interp1 (t, y, ti, 'pchip'); "
                     "out = struct ('ti', ti, 'ys', ys, 'yp', yp);"),
    "interpderiv2": ("t = -2:2; ti = -2:0.025:2; dti = 0.025; y = sign (t); "
                     "ddys = diff (diff (interp1 (t, y, ti, 'spline')) ./ dti) ./ dti; "
                     "ddyp = diff (diff (interp1 (t, y, ti, 'pchip')) ./ dti) ./ dti; "
                     "out = struct ('ti', ti(2:end-1), 'ddys', ddys, 'ddyp', ddyp);"),
}

BLUE, ORANGE, GREEN, RED = "#0072bd", "#d95319", "#00ff00", "#ff0000"  # Octave 默认色序的前两个；"g" "r" 是纯色


def octave_data(name: str) -> dict:
    if OCTAVE is None:
        raise SystemExit("需要本机 Octave 来计算图的数据")
    prog = DATA[name] + " printf ('%s', jsonencode (out));"
    r = subprocess.run([OCTAVE, "--no-gui", "--no-window-system", "--norc", "--quiet", "--eval", prog],
                       capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        raise SystemExit(f"{name}: Octave 失败：{r.stderr[-300:]}")
    return json.loads(r.stdout)


def draw(name: str, d: dict):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib import cm
    from mpl_toolkits.mplot3d.art3d import Line3DCollection

    plt.rcParams.update({"svg.fonttype": "path", "svg.hashsalt": f"octave-manual-{name}", "font.size": 9,
                         "axes.prop_cycle": matplotlib.cycler(color=[BLUE, ORANGE])})
    fig = plt.figure(figsize=(5.0, 3.5))
    if name == "plot":
        ax = fig.add_subplot()
        ax.plot(d["x"], d["y"])
        ax.set_xlabel("x"); ax.set_ylabel("sin (x)"); ax.set_title("Simple 2-D Plot")
    elif name == "hist":
        ax = fig.add_subplot()
        x, n = np.array(d["x"]), np.array(d["n"])
        ax.bar(x, n, width=(x[1] - x[0]), color=BLUE, edgecolor="black", linewidth=0.5)
        ax.set_xlabel("Value"); ax.set_ylabel("Count")
        ax.set_title("Histogram of 10,000 normally distributed random numbers", fontsize=8)
    elif name == "polar":
        ax = fig.add_subplot(projection="polar")
        t = np.array(d["t"])
        ax.plot(t, t)
        ax.set_title("Example polar plot from 0 to 10*pi")
    elif name == "mesh":
        ax = fig.add_subplot(projection="3d")
        x, y, z = np.array(d["x"]), np.array(d["y"]), np.array(d["z"])
        # mesh 画的是按高度着色的网格线（Octave 默认色图随高度变化）
        cmap, norm = cm.viridis, matplotlib.colors.Normalize(z.min(), z.max())
        segs, cols = [], []
        for i in range(len(y)):
            for j in range(len(x) - 1):
                segs.append([(x[j], y[i], z[i][j]), (x[j + 1], y[i], z[i][j + 1])]); cols.append(cmap(norm((z[i][j] + z[i][j + 1]) / 2)))
        for j in range(len(x)):
            for i in range(len(y) - 1):
                segs.append([(x[j], y[i], z[i][j]), (x[j], y[i + 1], z[i + 1][j])]); cols.append(cmap(norm((z[i][j] + z[i + 1][j]) / 2)))
        ax.add_collection3d(Line3DCollection(segs, colors=cols, linewidths=0.6))
        ax.set_xlim(x.min(), x.max()); ax.set_ylim(y.min(), y.max()); ax.set_zlim(z.min(), z.max())
        ax.set_xlabel("tx"); ax.set_ylabel("ty"); ax.set_zlabel("tz"); ax.set_title("3-D Sombrero plot")
    elif name == "plot3":
        ax = fig.add_subplot(projection="3d")
        ax.plot(d["x"], d["y"], d["z"])
        ax.set_xlabel("r.*sin (t)"); ax.set_ylabel("r.*cos (t)"); ax.set_zlabel("z")
        ax.set_title("plot3 display of 3-D helix")
    elif name == "interpderiv1":
        ax = fig.add_subplot()
        ax.plot(d["ti"], d["ys"], color=RED, label="spline"); ax.plot(d["ti"], d["yp"], color=GREEN, label="pchip")
        ax.legend(loc="lower right")
    elif name == "interpderiv2":
        ax = fig.add_subplot()
        ax.plot(d["ti"], d["ddys"], "*", color=RED, markersize=4, label="spline")
        ax.plot(d["ti"], d["ddyp"], "+", color=GREEN, markersize=4, label="pchip")
        ax.legend(loc="upper right")
    else:
        raise SystemExit(f"没有 {name} 的绘图代码")
    fig.tight_layout()
    return fig


def figure_names() -> list[str]:
    scope = json.loads((ROOT / "content" / "scope.json").read_text(encoding="utf-8"))
    return [f for part in scope["parts"] for it in part["items"] for f in it.get("figures", [])]


def main() -> int:
    want = sys.argv[1:] or figure_names()
    OUT.mkdir(parents=True, exist_ok=True)
    for name in want:
        if name not in DATA:
            print(f"跳过 {name}：没有对应的绘图代码", file=sys.stderr)
            continue
        fig = draw(name, octave_data(name))
        path = OUT / f"{name}.svg"
        fig.savefig(path, format="svg", metadata={"Date": None, "Creator": "athena octave-manual render_figures.py"})
        # 去掉 matplotlib 写进去的固定尺寸，交给 CSS 按容器缩放
        svg = path.read_text(encoding="utf-8")
        svg = re.sub(r'<svg([^>]*?) width="([\d.]+)pt" height="([\d.]+)pt"', r'<svg\1 width="\2pt" height="\3pt"', svg, count=1)
        path.write_text(svg, encoding="utf-8")
        print(f"写入 {path.relative_to(ROOT)}（{path.stat().st_size // 1024} KB）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
