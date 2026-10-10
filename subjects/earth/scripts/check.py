#!/usr/bin/env python3
"""Earth 的独立验证入口：数据 JSON、标准值核对（Python 侧独立复算），再前端构建、单元测试与 Rust 侧检查。"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 这里是 Python 侧独立抄录的标准值（出处见 content/earth.json 的 sources），
# 与前端 catalog.test.ts 互为备份：两边不是同一份代码，同时写错同一处数值的概率很小。
EXPECTED_MOHO_KM = 35
EXPECTED_410_KM = 410
EXPECTED_660_KM = 660
EXPECTED_CMB_KM = 2891
EXPECTED_ICB_KM = 5150
EXPECTED_EARTH_RADIUS_KM = 6371.0
EXPECTED_WGS84_INV_F = 298.257223563
EXPECTED_USSA_TEMP_C = [(0, 15.0), (11, -56.5), (20, -56.5), (32, -44.5), (47, -2.5), (51, -2.5), (71, -58.5), (86, -86.3)]
EXPECTED_ATMO_TOPS = {"troposphere": 12, "stratosphere": 50, "mesosphere": 85, "thermosphere": 600}


def force_utf8() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def tool(name: str) -> str:
    found = shutil.which(name)
    if found is None:
        raise SystemExit(f"找不到 {name}，请安装后重试")
    return found


def run(command: list[str], step: str) -> None:
    print(f"== {step} ==", flush=True)
    completed = subprocess.run(command, cwd=PROJECT_ROOT)
    if completed.returncode:
        raise SystemExit(completed.returncode)


def check_json() -> None:
    print("== 数据 JSON 解析 ==", flush=True)
    path = PROJECT_ROOT / "content" / "earth.json"
    try:
        json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise SystemExit(f"{path.relative_to(PROJECT_ROOT)}: {error}") from error
    try:
        json.loads((PROJECT_ROOT / "app.json").read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise SystemExit(f"app.json: {error}") from error
    print("earth.json 与 app.json 解析通过", flush=True)


def check_standards() -> None:
    """数据文件里的关键数值对照独立抄录的标准值（真实比例应用的底线，ADR 0128 决策 6）。"""
    print("== 标准值核对（Python 侧独立复算）==", flush=True)
    data = json.loads((PROJECT_ROOT / "content" / "earth.json").read_text(encoding="utf-8"))
    problems: list[str] = []

    shape = data["shape"]
    if abs(shape["meanRadiusKm"] - EXPECTED_EARTH_RADIUS_KM) > 1e-9:
        problems.append("平均半径不是 6371 km")
    if abs(shape["inverseFlattening"] - EXPECTED_WGS84_INV_F) > 1e-6:
        problems.append("WGS 84 扁率倒数与标准值不符")
    b_expected = shape["equatorialRadiusKm"] * (1 - 1 / shape["inverseFlattening"])
    if abs(shape["polarRadiusKm"] - b_expected) > 1e-3:
        problems.append("椭球参数不自洽：b ≠ a·(1−f)")

    layers = {layer["id"]: layer for layer in data["interior"]["layers"]}
    order = ["crust", "upper-mantle", "transition-zone", "lower-mantle", "outer-core", "inner-core"]
    if list(layers) != order:
        problems.append(f"内部分层的顺序或成员不对：{list(layers)}")
    for layer_id, expected_bottom in [
        ("crust", EXPECTED_MOHO_KM),
        ("upper-mantle", EXPECTED_410_KM),
        ("transition-zone", EXPECTED_660_KM),
        ("lower-mantle", EXPECTED_CMB_KM),
        ("outer-core", EXPECTED_ICB_KM),
        ("inner-core", EXPECTED_EARTH_RADIUS_KM),
    ]:
        actual = layers[layer_id]["bottomDepthKm"]
        if actual != expected_bottom:
            problems.append(f"{layer_id} 底界 {actual} km，标准值 {expected_bottom} km")
    for previous, following in zip(order, order[1:]):
        if layers[previous]["bottomDepthKm"] != layers[following]["topDepthKm"]:
            problems.append(f"{previous} 与 {following} 的层界不衔接")

    crust = layers["crust"]
    if not (5 <= crust["bottomDepthKmOceanic"] < crust["bottomDepthKmContinental"] <= 70):
        problems.append("地壳的大陆/大洋厚度声明不在文献区间内")

    # PREM：无缝覆盖、密度单调不减、地心值、古登堡面跳变
    segments = data["interior"]["premSegments"]
    if segments[0]["topDepthKm"] != 0 or segments[-1]["bottomDepthKm"] != EXPECTED_EARTH_RADIUS_KM:
        problems.append("PREM 分段没有覆盖 0–6371 km")
    for previous, following in zip(segments, segments[1:]):
        if previous["bottomDepthKm"] != following["topDepthKm"]:
            problems.append("PREM 分段不衔接")
        if following["topDensity"] < previous["bottomDensity"]:
            problems.append("PREM 界面处密度出现倒退")
    for segment in segments:
        if segment["bottomDensity"] < segment["topDensity"]:
            problems.append("PREM 段内密度随深度下降")
    if abs(segments[-1]["bottomDensity"] - 13.09) > 0.02:
        problems.append("地心密度不是 13.09 g/cm³")
    cmb_mantle = next(s for s in segments if s["bottomDepthKm"] == EXPECTED_CMB_KM)
    cmb_core = next(s for s in segments if s["topDepthKm"] == EXPECTED_CMB_KM)
    jump = cmb_core["topDensity"] - cmb_mantle["bottomDensity"]
    if not 4.0 <= jump <= 4.6:
        problems.append(f"古登堡面密度跳变 {jump:.2f} g/cm³，应在 4.0–4.6 之间")

    # 大气：WMO 界线、卡门线、USSA1976 折点
    atmo = {layer["id"]: layer for layer in data["atmosphere"]["layers"]}
    if list(atmo) != ["troposphere", "stratosphere", "mesosphere", "thermosphere", "exosphere"]:
        problems.append(f"大气分层的顺序或成员不对：{list(atmo)}")
    for layer_id, expected_top in EXPECTED_ATMO_TOPS.items():
        if atmo[layer_id]["topHeightKm"] != expected_top:
            problems.append(f"{layer_id} 顶界不是 {expected_top} km")
    if atmo["exosphere"]["topHeightKm"] is not None:
        problems.append("外逸层上界应不封闭（null）")
    if data["atmosphere"]["karmanLineKm"] != 100:
        problems.append("卡门线不是 100 km")
    actual_temp = [(p["heightKm"], p["tempC"]) for p in data["atmosphere"]["ussa1976"]["tempPointsC"]]
    for (expected_h, expected_t), (actual_h, actual_t) in zip(EXPECTED_USSA_TEMP_C, actual_temp):
        if expected_h != actual_h or abs(expected_t - actual_t) > 0.05:
            problems.append(f"USSA1976 折点 {actual_h} km 温度 {actual_t} °C，标准值 {expected_t} °C")
    if data["atmosphere"]["ussa1976"]["pressurePointsHPa"][0]["pressureHPa"] != 1013.25:
        problems.append("海平面气压不是 1013.25 hPa")

    # 出处：每个层与关键表都声明 sourceIds，且都能在源头目录解析
    sources = data["sources"]
    referenced = set(data["shape"]["sourceIds"] + data["surface"]["sourceIds"]
                     + data["interior"]["sourceIds"] + data["atmosphere"]["sourceIds"]
                     + data["atmosphere"]["ussa1976"]["sourceIds"]
                     + data["demos"]["sourceIds"])
    for group in (data["interior"]["layers"], data["atmosphere"]["layers"]):
        for entry in group:
            if not entry["sourceIds"]:
                problems.append(f"层 {entry['id']} 没有声明出处")
            referenced.update(entry["sourceIds"])
    for source_id in sorted(referenced):
        if source_id not in sources:
            problems.append(f"缺出处条目：{source_id}")
        elif not str(sources[source_id]["url"]).startswith("http"):
            problems.append(f"出处 {source_id} 的链接不是 http(s)")

    # 演示数据（ADR 0128 严谨口径的延伸）：射程是公开报道量级、弹道声明为示意、
    # 演示点是抽象的、机型参数是手册常识区间
    demos = data["demos"]
    if "示意" not in demos["ballisticNote"] or "示意" not in demos["launch"]["name"]:
        problems.append("弹道演示必须声明教学示意口径与抽象演示点")
    for spec in demos["ballistics"]:
        if spec["apogeeKm"] >= spec["rangeKm"]:
            problems.append(f"{spec['id']} 的顶点高度不低于射程，剖面不成立")
        if spec["name"].find("短程") >= 0 and spec["rangeKm"] >= 1000:
            problems.append(f"{spec['id']} 标为短程但射程 ≥ 1000 km")
        if "洲际" in spec["name"] and spec["rangeKm"] <= 10000:
            problems.append(f"{spec['id']} 标为洲际但射程 ≤ 10000 km")
        if "中程" in spec["name"] and not 1000 < spec["rangeKm"] < 5000:
            problems.append(f"{spec['id']} 标为中程但射程不在 1000–5000 km")
    for craft in demos["aircraft"]:
        if not 700 < craft["cruiseSpeedKmh"] < 3000:
            problems.append(f"{craft['id']} 巡航速度不在常识区间")
        if not 8 < craft["cruiseHeightKm"] < 25:
            problems.append(f"{craft['id']} 巡航高度不在常识区间")

    if problems:
        for problem in problems:
            print(f"  · {problem}", flush=True)
        raise SystemExit(f"标准值核对未通过，共 {len(problems)} 处。")
    print(
        "WGS 84、六层内部结构、PREM 界面值、WMO 大气界线、USSA1976 廓线、出处闭环全部核对通过",
        flush=True,
    )


def ensure_dependencies() -> None:
    if (PROJECT_ROOT / "node_modules").is_dir():
        return
    # 有 lock 就按 lock 装：CI 上每次拿到的依赖要和本地一致。
    npm = tool("npm")
    if (PROJECT_ROOT / "package-lock.json").is_file():
        run([npm, "ci"], "安装前端依赖（按 lock）")
    else:
        run([npm, "install"], "安装前端依赖")


def main() -> int:
    force_utf8()
    parser = argparse.ArgumentParser(description="验证 Earth：数据标准值、前端与壳")
    parser.add_argument(
        "--skip-rust",
        action="store_true",
        help="跳过 Rust 侧检查（只改了数据或前端时用它，能省几分钟）",
    )
    arguments = parser.parse_args()

    check_json()
    check_standards()
    ensure_dependencies()
    npm = tool("npm")
    # npm run build = tsc -b + vite build，类型和打包一次过。
    run([npm, "run", "build"], "前端类型检查与构建")
    run([npm, "test"], "前端单元测试（标准值、探针换算、装配冒烟）")
    if not arguments.skip_rust:
        run(
            [tool("cargo"), "check", "--manifest-path", "src-tauri/Cargo.toml", "--all-targets"],
            "Rust 侧检查",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
