#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""裁 Natural Earth 灰度晕渲到东亚，写出 ≤3MB WebP（入库）与 .cache 原图。

用法：
  python packages/maps/scripts/prepare_relief.py

验收框：lon 70–145、lat 15–55（青藏高原 / 秦岭 / 太行 / 横断 / 四川盆地）。
"""

from __future__ import annotations

import io
import sys
import zipfile
from pathlib import Path
from urllib.request import urlretrieve

import math

import numpy as np
from PIL import Image

REPO = Path(__file__).resolve().parents[3]
CACHE = REPO / ".cache" / "maps" / "natural-earth"
OUT = REPO / "packages" / "maps" / "geo" / "relief-east-asia.webp"
META = REPO / "packages" / "maps" / "geo" / "relief-east-asia.json"

# GRAY_50M_SR_OB：灰度晕渲 + 海洋底；Plate Carrée 全球
URL = "https://naciscdn.org/naturalearth/50m/raster/GRAY_50M_SR_OB.zip"
WEST, EAST, SOUTH, NORTH = 70.0, 145.0, 15.0, 55.0
MAX_BYTES = 3 * 1024 * 1024


def lonlat_to_px(lon: float, lat: float, w: int, h: int) -> tuple[float, float]:
    x = (lon + 180.0) / 360.0 * w
    y = (90.0 - lat) / 180.0 * h
    return x, y


def mercator_y(lat: float) -> float:
    return math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


def equirect_to_mercator_rows(img: Image.Image, north: float, south: float) -> Image.Image:
    """把「纬度均匀」的栅格重采样成「Web 墨卡托 y 均匀」的栅格（经度方向不变）。

    为什么必须做：NE 栅格是 Plate Carrée（行与纬度成线性），而 MapLibre 的 image source 只给四个角点，
    会把图像在**墨卡托空间里线性拉伸**。两者不一致，晕渲会整体向北偏移，纬度 35° 附近偏约 2.6°（约 290 km），
    于是城市点（矢量，位置是对的）和底图山河海岸对不上。预先按墨卡托行重采样，四角点拉伸才是正确的。
    """
    w, h = img.size
    arr = np.asarray(img, dtype=np.float32)
    y_n, y_s = mercator_y(north), mercator_y(south)
    # 保持像素近似正方：墨卡托范围宽 = 经度跨度（弧度），高 = y 差
    lon_span = math.radians(EAST - WEST)
    out_h = max(2, int(round(w * (y_n - y_s) / lon_span)))
    out = np.empty((out_h, w), dtype=np.float32)
    for j in range(out_h):
        yy = y_n - (y_n - y_s) * (j + 0.5) / out_h
        lat = math.degrees(2 * math.atan(math.exp(yy)) - math.pi / 2)
        r = (north - lat) / (north - south) * h - 0.5
        r = min(max(r, 0.0), h - 1.0)
        r0 = int(math.floor(r))
        r1 = min(r0 + 1, h - 1)
        f = r - r0
        out[j] = arr[r0] * (1 - f) + arr[r1] * f
    return Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8), mode="L")


def main() -> int:
    CACHE.mkdir(parents=True, exist_ok=True)
    zpath = CACHE / "GRAY_50M_SR_OB.zip"
    if not zpath.is_file() or zpath.stat().st_size < 1_000_000:
        print(f"下载 {URL} …")
        urlretrieve(URL, zpath)
        print(f"已下载 {zpath.stat().st_size / 1e6:.1f} MB")

    img: Image.Image | None = None
    with zipfile.ZipFile(zpath) as zf:
        names = [n for n in zf.namelist() if n.lower().endswith((".tif", ".tiff", ".jpg", ".jpeg", ".png"))]
        if not names:
            print("zip 内无栅格", file=sys.stderr)
            return 1
        # 优先 tif
        names.sort(key=lambda n: (0 if n.lower().endswith((".tif", ".tiff")) else 1, len(n)))
        raw = zf.read(names[0])
        print(f"解压 {names[0]} ({len(raw) / 1e6:.1f} MB)")
        img = Image.open(io.BytesIO(raw))
        img.load()

    assert img is not None
    w, h = img.size
    print(f"原图 {w}×{h} mode={img.mode}")
    x0, y0 = lonlat_to_px(WEST, NORTH, w, h)
    x1, y1 = lonlat_to_px(EAST, SOUTH, w, h)
    box = (int(x0), int(y0), int(x1), int(y1))
    crop = img.crop(box).convert("L")
    print(f"裁切 {box} → {crop.size}")
    crop = equirect_to_mercator_rows(crop, NORTH, SOUTH)
    print(f"按墨卡托行重采样 → {crop.size}")

    # 控制边长，优先清晰山脉
    max_side = 2400
    if max(crop.size) > max_side:
        crop.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    quality = 80
    while quality >= 40:
        buf = io.BytesIO()
        crop.save(buf, format="WEBP", quality=quality, method=6)
        data = buf.getvalue()
        if len(data) <= MAX_BYTES:
            OUT.write_bytes(data)
            print(f"写出 {OUT}  {len(data) / 1e6:.2f} MB  q={quality}")
            break
        quality -= 5
    else:
        OUT.write_bytes(data)
        print(f"警告：仍超 3MB → {len(data) / 1e6:.2f} MB", file=sys.stderr)

    meta = {
        "west": WEST,
        "east": EAST,
        "south": SOUTH,
        "north": NORTH,
        "source": "Natural Earth GRAY_50M_SR_OB",
        "file": "relief-east-asia.webp",
        "opacity": 0.35,
        "projection": "web-mercator-rows",
        "blend": "multiply",
    }
    META.write_text(
        __import__("json").dumps(meta, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"写出 {META}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
