# -*- coding: utf-8 -*-
"""生成 T-001 题库草稿：手写干扰项、答案摊匀、预测题带 figure/reveal。

返工约束（leader 2026-10-19）：
- choices 一律不许有括号注释（「（」「(」都不行）
- 正确项为最长的题占全课 20%~35%，每章不超过 1/3；不要刻意压到 0
- 干扰项手写，像真错；长度与正确项差不超过 40%
"""
from __future__ import annotations

import json
import pathlib
import re
from collections import Counter

OUT = pathlib.Path(__file__).resolve().parent
QDIR = OUT / "questions"

SELF = lambda loc: {
    "relation": "authored",
    "source_id": "self-authored",
    "locator": loc,
    "note": "对应本章讲解与程序中的真实函数/性质，没有现成题，自拟。",
}
WIKI_P = {
    "relation": "authored",
    "source_id": "wikipedia-pocket-cube",
    "locator": "结构与位置数",
    "note": "条目只给出结构/位置数要点；本题按本课程讲解自拟，没有现成中文题。",
}
WIKI_R = {
    "relation": "authored",
    "source_id": "wikipedia-rubiks-cube",
    "locator": "标准配色",
    "note": "对面配对来自条目；题目按本课程姿势自拟。",
}

PAREN_RE = re.compile(r"[（(]")


def place(correct: str, wrongs: list[str], answer: int) -> list[str]:
    assert len(wrongs) == 3 and 0 <= answer <= 3
    slots: list[str] = []
    wi = 0
    for i in range(4):
        if i == answer:
            slots.append(correct)
        else:
            slots.append(wrongs[wi])
            wi += 1
    return slots


def cube_fig(title, caption, *, setup="", moves=None, expect=None, marks=None):
    fig = {"kind": "cube", "title": title, "caption": caption, "setup": setup}
    if moves is not None:
        fig["moves"] = moves
    if expect is not None:
        fig["expect"] = expect
    if marks is not None:
        fig["marks"] = marks
    return fig


def q(id, kind, stem, correct, wrongs, answer, explanation, refs, **viz):
    item = {
        "id": id,
        "kind": kind,
        "stem": stem,
        "choices": place(correct, wrongs, answer),
        "answer": answer,
        "explanation": explanation,
        "source_refs": refs,
    }
    item.update(viz)
    return item


# 答案位置预先摊匀：全课每个位置约 25%
ANS = {
    "cube.net.count": 0,
    "cube.net.index": 1,
    "cube.net.colors": 2,
    "cube.net.separation": 3,
    "cube.net.predict-ruprime": 0,
    "cube.turns.notation": 1,
    "cube.turns.three": 2,
    "cube.turns.order": 3,
    "cube.turns.derived": 0,
    "cube.turns.animation": 1,
    "cube.turns.predict-ru": 2,
    "cube.turns.disc-anim-state": 3,
    "cube.turns.recall-net-slot": 0,
    "cube.layer.done": 1,
    "cube.layer.keep": 2,
    "cube.layer.iddfs": 3,
    "cube.layer.prune": 0,
    "cube.layer.predict-rprime": 1,
    "cube.layer.disc-done-vs-solved": 2,
    "cube.layer.recall-dbl": 3,
    "cube.orient.sune": 0,
    "cube.orient.done": 1,
    "cube.orient.search": 2,
    "cube.orient.cases": 3,
    "cube.orient.predict-sune": 0,
    "cube.orient.disc-sune-antisune": 1,
    "cube.orient.recall-layer-done": 2,
    "cube.permute.formulas": 3,
    "cube.permute.order": 0,
    "cube.permute.count": 1,
    "cube.permute.length": 2,
    "cube.permute.predict-r2": 3,
    "cube.permute.disc-pos-vs-ori": 0,
    "cube.permute.recall-iddfs": 1,
    "cube.solver.legal": 2,
    "cube.solver.count": 3,
    "cube.solver.normalize": 0,
    "cube.solver.frame": 1,
    "cube.solver.predict-f": 2,
    "cube.solver.disc-diagnose-normalize": 3,
    "cube.solver.recall-pipeline": 0,
    "cube.optimal.table": 1,
    "cube.optimal.god": 2,
    "cube.optimal.byte": 3,
    "cube.optimal.descent": 0,
    "cube.optimal.predict-ur": 1,
    "cube.optimal.disc-bfs-vs-layer": 2,
    "cube.optimal.recall-count": 3,
}


def A(qid: str) -> int:
    return ANS[qid]


# 计划让正确项成为最长的题（约 13/48 ≈ 27%），每章 ≤1/3：
# 01 separation；02 three, derived；03 done, iddfs；04 sune, search；
# 05 formulas, order；06 legal, normalize；07 table, disc-bfs-vs-layer
CHAPTERS: dict[str, list] = {
    "01-net": [
        q(
            "cube.net.count",
            "重点",
            "2 阶魔方一共有多少张贴纸？它们和角块是什么关系？",
            "24 张；8 个角块，每个角块上 3 张",
            [
                "24 张；6 个角块，每个角块上 4 张",
                "48 张；8 个角块，每个角块上 6 张",
                "12 张；4 个角块，每个角块上 3 张",
            ],
            A("cube.net.count"),
            "6 面 × 每面 4 格 = 24；也可按角块：8 × 3。"
            "「6 个角块」把角块数记成了面数；「48 张」是把每面当成了 3×3；"
            "「12 张 / 4 角」则少算了半个立方。",
            [WIKI_P],
        ),
        q(
            "cube.net.index",
            "重点",
            "展开图里第 13 号贴纸（从 0 数）属于哪个面？",
            "D 面",
            ["U 面", "R 面", "F 面"],
            A("cube.net.index"),
            "13 ÷ 4 = 3 余 1。面序 U R F D L B，下标 3 是 D。"
            "选 U/R/F 多半是把余数或面序起点记错了。",
            [SELF("第 1 章 · 贴纸编号")],
        ),
        q(
            "cube.net.colors",
            "难点",
            "复原态下，哪一种颜色组合不可能出现在同一个角块上？",
            "黄、白、绿",
            ["黄、绿、橙", "白、蓝、红", "白、绿、橙"],
            A("cube.net.colors"),
            "黄白是对面，角块碰不到一对相对面。其余三项都是三个两两相邻的面，可以同角。",
            [WIKI_R],
        ),
        q(
            "cube.net.separation",
            "考点",
            "NetView 为什么不自己判断「点的这格属于哪个角块」？",
            "角块含义属于魔方本身，放在 cube；视图只负责画和报告点了哪一格",
            [
                "角块对照表应由视图缓存，点格时直接在 NetView 里查完",
                "信号机制一次只能传像素坐标，没法再把角块编号带回去",
                "Session 只做接线，所有角块语义都必须压进自绘控件内部",
            ],
            A("cube.net.separation"),
            "数据在 cube，画在 NetView，接线在 Session。"
            "把对照表塞进视图、或以为信号带不了 slot、或把语义全塞进控件，都会把职责划乱。",
            [SELF("第 1 章 · 职责划分")],
        ),
        q(
            "cube.net.predict-ruprime",
            "重点",
            "从复原态做 R U' R'，U 面左上那一格（展开图 U 面第 0 格）是什么颜色？",
            "绿色",
            ["黄色", "橙色", "白色"],
            A("cube.net.predict-ruprime"),
            "R 把 UFR 的绿转到 U，U' 再把它转到 U 面左上（slot 0）。实算为绿。"
            "黄是复原态原色；橙/白是把别的面贴纸误当成了终点。",
            [SELF("第 1 章展开图；第 2 章转动")],
            figure=cube_fig("起点", "复原态", setup=""),
            reveal=cube_fig("走一遍", "R 然后 U' 然后 R'", setup="", moves="R U' R'"),
        ),
    ],
    "02-turns": [
        q(
            "cube.turns.notation",
            "重点",
            "记号 R' 表示什么？",
            "右面逆时针转 90°",
            ["右面顺时针转 90°", "右面转 180°", "把整个魔方向右翻转"],
            A("cube.turns.notation"),
            "单独字母顺时针，加撇逆时针，加 2 半圈；顺逆都从该面外面看。"
            "顺时针是漏了撇；180° 是 R2；整体翻转不是单面转动。",
            [SELF("第 2 章 · 记号")],
        ),
        q(
            "cube.turns.three",
            "重点",
            "为什么只用 U、R、F 三个面就够了？",
            "因为 2 阶魔方没有中心块，转 D、L、B 等于整体换姿势再转 U、R、F",
            [
                "因为机构限制导致 D、L、B 三个面在物理上根本转不动",
                "因为 U、R、F 碰到的角块更多，覆盖面比另外三面更广",
                "因为解题手册规定禁止写下 D、L、B，与几何是否等价无关",
            ],
            A("cube.turns.three"),
            "无中心块就无固定朝向参照。转 D 等价换姿势再转 U；DBL 可当不动参照。"
            "不是机构转不动，也不是覆盖面更大，更不是手册禁写。",
            [WIKI_P],
        ),
        q(
            "cube.turns.order",
            "要点",
            "从复原态起，R U R' U' 要重复几遍才回到复原？",
            "6 遍",
            ["4 遍", "8 遍", "12 遍"],
            A("cube.turns.order"),
            "测试逐遍检查：前 5 遍未复原，第 6 遍复原；回放共 24 步即六遍。"
            "4/8/12 是把交换群阶数或总步数误当成了重复遍数。",
            [SELF("第 2 章 · 转动的性质")],
        ),
        q(
            "cube.turns.derived",
            "难点",
            "转动的置换表为什么从坐标算出来，不直接手写？",
            "手写 18 张表很容易抄错，错了还看不出来；几何算出的方向和手性不会错",
            [
                "手写常量在编译期就会被类型系统拦住，所以抄错也不必担心",
                "坐标推导只服务调试版本，发布版仍应改回十八张手写表",
                "查表启动太慢，运行期现算坐标反而比预存置换更省事",
            ],
            A("cube.turns.derived"),
            "表错一格会悄悄变成另一个魔方。几何结果还能用 U⁴=1 交叉验证。"
            "类型系统拦不住「写进错误的下标」；发布版同样用推导表；"
            "现算坐标也不是为了启动速度，而是为了正确性。",
            [SELF("第 2 章 · 转动是算出来的")],
        ),
        q(
            "cube.turns.animation",
            "考点",
            "一步转动的动画放到一半时，Session 里存的魔方状态是什么？",
            "转之前的状态，转完 finish 才换",
            [
                "已经是转完之后写进 Session 的最终状态",
                "一个按中间角度插值出来的半合法状态",
                "被清空之后暂时不持有任何贴纸颜色的空状态",
            ],
            A("cube.turns.animation"),
            "动画只是画面。finish 里才 perform 换状态。"
            "「已经是终态」把画面当成了提交；「半状态」把插值角当成合法态；空状态更无依据。",
            [SELF("第 2 章 · 动画不是状态")],
        ),
        q(
            "cube.turns.predict-ru",
            "重点",
            "从复原态做 R U，F 面右上那一格（展开图 F 面第 1 行右格）前面是什么颜色？",
            "橙色",
            ["黄色", "绿色", "白色"],
            A("cube.turns.predict-ru"),
            "R 先把橙面贴纸转到 F 右上；U 不改变该 F 面格颜色。实算 slot 9 为橙。"
            "黄/绿/白是复原态邻格常见色，容易在心理模拟时串面。",
            [SELF("第 2 章 · 记号与转动")],
            figure=cube_fig("起点", "复原态", setup=""),
            reveal=cube_fig("走一遍", "R 然后 U", setup="", moves="R U", marks=[9]),
        ),
        q(
            "cube.turns.disc-anim-state",
            "难点",
            "下面哪一句把「画面上的转动」和「Session 里的状态」分清楚了？",
            "动画只改画面；状态要等 finish 才 perform 更换",
            [
                "动画放到一半时，Session 里保存的状态其实已经是转完后的最终结果",
                "动画中插值出来的中间角度本身就是一个合法魔方状态",
                "点撤销会立刻改写状态，完全不必等待当前动画播放结束",
            ],
            A("cube.turns.disc-anim-state"),
            "画面可插值，状态只有转完才换。把半动画当已提交、当合法态，"
            "或以为撤销可插队改状态，都会弄错队列与撤销。",
            [SELF("第 2 章 · 动画不是状态")],
        ),
        q(
            "cube.turns.recall-net-slot",
            "要点",
            "要判断「展开图第 9 号贴纸属于哪一面、转完 U/R/F 后编号是否仍属该面」，需要先掌握第 1 章的哪条约定？",
            "编号标的是格子位置；转动只换颜色，面属不变",
            [
                "编号跟着色块走，转到哪一面编号就改属哪一面",
                "编号只在复原态有效，一旦打乱就必须重新编号",
                "编号按角块编号排列，与面序 U R F D L B 无关",
            ],
            A("cube.turns.recall-net-slot"),
            "9÷4=2 余 1，面序第三是 F。第 1 章规定编号标格子，颜色搬家、面属不变。"
            "「跟着色块走」「打乱重编号」「按角块排」都是把编号语义记反了。",
            [SELF("第 1 章 · 贴纸编号；第 2 章转动")],
        ),
    ],
    "03-layer": [
        q(
            "cube.layer.done",
            "重点",
            "layer_done 判定第一层完成，检查的是哪些角块位置？",
            "DFR、DLF、DRB 加上永远不动的 DBL，一共检查 4 个底层角块位置",
            [
                "只检查 DFR、DLF、DRB 三个会被 U/R/F 碰到的活动角块位置",
                "只检查顶层四个角块是不是已经全部回到各自原来的位置",
                "一次把全部八个角块的位置是否都已经完全复原检查完毕",
            ],
            A("cube.layer.done"),
            "底层四角。DBL 不被 U/R/F 碰到，实际装另外三块，判定时四个一起看。"
            "漏掉 DBL、改看顶层、或要求整立方复原，都把完成条件记宽或记偏了。",
            [SELF("第 3 章 · layer_done")],
        ),
        q(
            "cube.layer.keep",
            "重点",
            "装第 2 块时，为什么第 1 块也算搜索的目标？",
            "否则搜索可能为了装第 2 块把已经装好的第 1 块拆掉",
            [
                "只是为了让搜索树分叉更少、整体跑得更快一些而已",
                "因为两块在几何上必须在同一时刻被同一转法带动",
                "因为评分函数里第 1 块的权重被设得比第 2 块更高一些",
            ],
            A("cube.layer.keep"),
            "目标是「前 k 块都在原位」。装好的块被保护，后面不会被碰坏。"
            "加速、共转、权重都不是把第 1 块写进目标的理由。",
            [SELF("第 3 章 · search 的 placed 参数")],
        ),
        q(
            "cube.layer.iddfs",
            "难点",
            "迭代加深为什么能保证第一次成功的就是最短装法？",
            "因为它从浅到深一层一层试，更浅的层已经全部失败过了",
            [
                "因为它在每一层内部都优先扩展看起来更短的那条转法",
                "因为它直接查了预先算好的全局距离表来裁剪分支",
                "因为它靠随机抽样，而抽样命中的路径统计上就是最短",
            ],
            A("cube.layer.iddfs"),
            "先穷尽 1 步再试 2 步。首次成功时更浅深度皆无解，故不会更短。"
            "层内启发式、距离表、随机抽样都不是本章迭代加深的保证来源。",
            [SELF("第 3 章 · 迭代加深")],
        ),
        q(
            "cube.layer.prune",
            "考点",
            "搜索时为什么可以不让同一个面连着转两次？",
            "U U 可并成 U2，U U' 会抵消，都不会更短，不必单独搜",
            [
                "因为同一面若连着转两次会把整个机构卡死，物理上根本就再也转不动了",
                "因为 R、U、F 三面在任何合法序列里根本不允许相邻出现",
                "因为连转同一面会把参照角块 DBL 从底层固定位置上弄走",
            ],
            A("cube.layer.prune"),
            "同面连续转动总能合并或抵消。剪掉后每层分叉 9→6。"
            "不是机构卡死，也不是三面不能相邻，更不会弄走 DBL。",
            [SELF("第 3 章 · 剪枝")],
        ),
        q(
            "cube.layer.predict-rprime",
            "重点",
            "从复原态只做一步 R'，此时 layer_done 与 is_solved 分别是什么？",
            "layer_done 为假，is_solved 也为假",
            [
                "layer_done 为真，is_solved 也为真",
                "layer_done 为真，is_solved 仍为假",
                "layer_done 为假，is_solved 反为真",
            ],
            A("cube.layer.predict-rprime"),
            "R' 动到底层角块，第一层不再完整，整立方也不复原，故两个谓词都为假。"
            "其余三项把两个谓词的真假组合记错了。",
            [SELF("第 3 章 · layer_done")],
            figure=cube_fig("起点", "复原态", setup=""),
            reveal=cube_fig("走一遍", "只做 R'", setup="", moves="R'"),
        ),
        q(
            "cube.layer.disc-done-vs-solved",
            "难点",
            "layer_done 为真、is_solved 为假，说明魔方处于哪种阶段？",
            "第一层已完成，但顶层角块尚未全部归位复原",
            [
                "第一层尚未完成，顶层四个角也完全没有被动过",
                "整立方其实已经复原，只是两个判定函数碰巧写反了",
                "只有顶面朝向完成，底层四角反而已经被拆散了",
            ],
            A("cube.layer.disc-done-vs-solved"),
            "layer_done 只看底层四角；is_solved 要求 24 格全对。"
            "底层好而整体未复原，正是进入阶段 2/3 的典型状态。",
            [SELF("第 3 章 · layer_done；复原判定")],
        ),
        q(
            "cube.layer.recall-dbl",
            "要点",
            "层先法只转 U、R、F 就能装好第一层——要理解这一点，需要先掌握第 2 章的哪条结论？",
            "无中心块时转 D/L/B 等价换姿势再转 U/R/F，因而可固定 DBL",
            [
                "程序把 D 面写成了禁止转动的非法操作，所以解题时只能用三面",
                "第一层角块在几何上从不出现在 D 面附近，所以完全不必转 D",
                "layer_done 故意跳过所有 D 面贴纸，因此转不转 D 都无所谓",
            ],
            A("cube.layer.recall-dbl"),
            "第 2 章结论：固定 DBL、只用三面，后面各阶段完成条件才站得住。"
            "不是禁操作、不是角块不到 D、也不是判定故意漏检。",
            [SELF("第 2 章 · 只用三面；第 3 章第一层")],
        ),
    ],
    "04-orient": [
        q(
            "cube.orient.sune",
            "重点",
            "公式 Sune 对魔方做了什么？",
            "不动第一层，只改变顶层角块的朝向，并顺带挪动它们的位置",
            [
                "把当前打乱的整个魔方一次性全部恢复到复原态",
                "只交换顶层两个角的位置，完全不改任何角的朝向",
                "只空转顶层一圈，其它所有贴纸的颜色都保持不动",
            ],
            A("cube.orient.sune"),
            "顶层朝向变、第一层不动；位置会顺带变。cube_test 对复原态做一次即断言此事。"
            "「整立方复原」「只换位」「只空转 U」都不是 Sune 的作用。",
            [SELF("第 4 章 · Sune")],
        ),
        q(
            "cube.orient.done",
            "重点",
            "top_oriented 怎样判定阶段 2 完成？",
            "U 面的 4 格都是黄色",
            [
                "顶层 4 个角块都在原位",
                "第一层和顶层都复原",
                "顶层 4 个角块朝向之和为 0",
            ],
            A("cube.orient.done"),
            "阶段 2 只要求黄色朝上，不管位置。U 面四格皆黄即四角黄色都朝上。"
            "「都在原位」是阶段 3；「都复原」是最终；「朝向和为 0」不是本章谓词。",
            [SELF("第 4 章 · top_oriented")],
        ),
        q(
            "cube.orient.search",
            "难点",
            "为什么阶段 2 不写「遇到这种情形就这样转」的分支，而用最短路搜索？",
            "状态不多，按总步数搜最短组合即可；手写分支表容易漏情形，也更难验证",
            [
                "分支表这种多路跳转结构在本课程用的语言里根本写不出来",
                "最短路搜索占用的内存一定比手写分支表更小，所以必须搜",
                "整个阶段从头到尾只用得到一个固定公式，搜索只是多余包装",
            ],
            A("cube.orient.search"),
            "可达状态只有几千。搜索通吃一切情形；测试确认随机打乱能做完即可。"
            "不是语言写不出分支，也不是内存必然更小，更不是「只用一个公式」。",
            [SELF("第 4 章 · 宏的最短路")],
        ),
        q(
            "cube.orient.cases",
            "考点",
            "顶层朝向还没完成的情形一共 7 种（转 U 算同一种）。其中恰好有 1 个黄色朝上的有几种？",
            "2 种",
            ["1 种", "3 种", "4 种"],
            A("cube.orient.cases"),
            "0 黄 2 种、1 黄 2 种（Sune/反 Sune 各一）、2 黄 3 种，共 7。"
            "其余数字是把某一档情形数记串了。",
            [SELF("第 4 章 · 七种情形")],
        ),
        q(
            "cube.orient.predict-sune",
            "重点",
            "从复原态做一次 Sune（R U R' U R U2 R'）后，U 面有几格黄色？layer_done 是否仍为真？",
            "1 格黄，且 layer_done 为真",
            [
                "0 格黄，且 layer_done 为假",
                "2 格黄，且 layer_done 为真",
                "4 格黄，且 layer_done 为真",
            ],
            A("cube.orient.predict-sune"),
            "实算 U 面只剩 1 黄；Sune 不动第一层，故 layer_done 仍真。"
            "0/2/4 黄是把七种情形里的其它档记到了这次操作上。",
            [SELF("第 4 章 · Sune")],
            figure=cube_fig("起点", "复原态", setup=""),
            reveal=cube_fig(
                "走一遍",
                "一次 Sune",
                setup="",
                moves="R U R' U R U2 R'",
                expect="layer",
            ),
        ),
        q(
            "cube.orient.disc-sune-antisune",
            "难点",
            "Sune 与反 Sune 最容易混在哪一点？",
            "二者互为逆：一个拧朝向，另一个沿反方向拧回去",
            [
                "二者转法序列完全相同，只是中文名字不同而已",
                "二者都会拆掉第一层，差别只在拆开底层的方向相反",
                "二者只交换顶层角的位置，完全不碰任何角的朝向",
            ],
            A("cube.orient.disc-sune-antisune"),
            "反 Sune 是 Sune 的逆。讲解用「Sune 再反 Sune」回到复原来验证。"
            "同序列异名、拆第一层、只换位，都是把二者关系记错了。",
            [SELF("第 4 章 · Sune 与反 Sune")],
        ),
        q(
            "cube.orient.recall-layer-done",
            "要点",
            "要用「对复原态做一次 Sune 后断言第一层仍完成」来验收公式，需要先掌握前面哪一章的概念？",
            "第 3 章的 layer_done：它定义了「第一层完成」到底检查哪些角",
            [
                "第 7 章距离表里的一列字段：专门用来标记第一层是否已经完成",
                "第 2 章的动画队列机制：finish 回调里会自动把底层四角恢复",
                "第 5 章的换位公式性质：换位之后 layer_done 会顺带被重新置位",
            ],
            A("cube.orient.recall-layer-done"),
            "完成条件来自第 3 章 layer_done；测试直接复用该谓词，不靠口诀。"
            "距离表、动画队列、换位公式都不是这条断言所依赖的前置概念。",
            [SELF("第 3 章 · layer_done；第 4 章测试")],
        ),
    ],
    "05-permute": [
        q(
            "cube.permute.formulas",
            "重点",
            "两个换位公式（相邻、对角）有什么共同点？",
            "都只交换顶层两个角块的位置，第一层和顶层朝向都保持不变",
            [
                "都会把当前打乱的整个魔方直接恢复到完全复原状态",
                "都会改写顶层角块的朝向，同时让它们的位置保持不动",
                "都只允许转动 U 面，其它面在整段公式里一步都不出现",
            ],
            A("cube.permute.formulas"),
            "测试对复原态各做一次：底层完好、U 仍黄、恰好两处位置变了。"
            "「整立方复原」「只改朝向」「只转 U」都不是这两个公式的共性。",
            [SELF("第 5 章 · 两个换位公式")],
        ),
        q(
            "cube.permute.order",
            "难点",
            "为什么必须先翻顶面、再摆顶层？",
            "因为换位公式不改朝向：朝向没翻好就换位，永远复原不了",
            [
                "因为摆顶层用到的公式平均长度比翻顶面那一段更长",
                "因为翻顶面占用了 U 面，而摆顶层公式在讲解里从不转 U",
                "没有几何或代数上的理由，只是手册里沿用的书写习惯",
            ],
            A("cube.permute.order"),
            "后一阶段公式假定前一阶段结果成立。换位只换位置，不会把拧着的角翻正。"
            "不是比长度、不是摆顶层从不转 U，更不是纯书写习惯。",
            [SELF("第 5 章 · 阶段的次序")],
        ),
        q(
            "cube.permute.count",
            "要点",
            "2 万个随机打乱里，阶段 3 最多用了几次换位公式？",
            "1 次",
            ["0 次", "2 次", "3 次"],
            A("cube.permute.count"),
            "转 U 加一个换位即可覆盖顶层 24 种排法；约六分之一只转 U。"
            "0 次是「最多」的下界误读；2/3 次是把平均或别的统计记串了。",
            [SELF("第 5 章 · 实测")],
        ),
        q(
            "cube.permute.length",
            "考点",
            "三个阶段合起来，层先法平均要多少步？",
            "约 35 步",
            ["约 10 步", "约 20 步", "约 90 步"],
            A("cube.permute.length"),
            "平均约 9 + 12.5 + 13.5 ≈ 35 步，最长 48 步（2 万次实测）。"
            "10/20 偏短，90 则把最长或其它度量记过头了。",
            [SELF("第 5 章 · 能解，但不短")],
        ),
        q(
            "cube.permute.predict-r2",
            "重点",
            "从复原态做 R2 之后，top_oriented 与 layer_done 分别是什么？",
            "top_oriented 为假，layer_done 也为假",
            [
                "top_oriented 为真，layer_done 也为真",
                "top_oriented 为真，layer_done 仍为假",
                "top_oriented 为假，layer_done 反为真",
            ],
            A("cube.permute.predict-r2"),
            "R2 对调底层与顶层角，U 面不再全黄，底层也不完整，故两个谓词都为假。"
            "其余组合是把两个谓词记反或只对了一半。",
            [SELF("第 4 章 top_oriented；第 3 章 layer_done")],
            figure=cube_fig("起点", "复原态", setup=""),
            reveal=cube_fig("走一遍", "只做 R2", setup="", moves="R2"),
        ),
        q(
            "cube.permute.disc-pos-vs-ori",
            "难点",
            "「角块的位置」和「角块的朝向」在阶段 2、3 里分别由谁负责？",
            "阶段 2 翻朝向，用 top_oriented；阶段 3 换位置，用换位公式",
            [
                "阶段 2 先换位置，阶段 3 再翻朝向，两个阶段的次序刚好相反",
                "两个阶段都只改位置，朝向完全要靠打乱时偶然已经正确",
                "两个阶段都只改朝向，位置要留到第 7 章查距离表时再处理",
            ],
            A("cube.permute.disc-pos-vs-ori"),
            "阶段 2 目标黄色朝上；阶段 3 换位只动位置。次序不能反。"
            "对调阶段、或以为某一维靠偶然/留给最短解，都是职责记混。",
            [SELF("第 4–5 章 · 阶段目标")],
        ),
        q(
            "cube.permute.recall-iddfs",
            "要点",
            "阶段 1「第一次搜到的装法可当最短」——要采信这句话，需要先掌握第 3 章的哪一点？",
            "迭代加深从浅到深穷尽；更浅层已失败，故首次成功即最短",
            [
                "随机打乱之后，搜索树里第一条成功路径在统计上总是最短",
                "换位公式保证每个角块装入第一层时恰好只需要一步转动",
                "阶段 1 开始前已经建好全局距离表，装块时直接查表取最短",
            ],
            A("cube.permute.recall-iddfs"),
            "依据是第 3 章迭代加深的完备性，不是随机运气、换位公式或距离表。",
            [SELF("第 3 章 · 迭代加深；第 5 章流水线")],
        ),
    ],
    "06-solver": [
        q(
            "cube.solver.legal",
            "重点",
            "下面哪一种涂色，是真魔方永远转不出来的？",
            "每种颜色仍是 4 格，但有一个角块被原地拧了一下，其余格子都对",
            [
                "把已经复原的魔方整个翻过来，换一个姿势重新放下",
                "从复原态出发连续打乱 20 步之后得到的任意一个状态",
                "只把右手那一面相对于复原态转了 90°，其它面都还没动",
            ],
            A("cube.solver.legal"),
            "拧一角会让朝向之和不是 3 的倍数；真魔方每次转动都保持该不变量。"
            "整体换姿势、合法打乱、单面转 90° 都是可到达状态。",
            [WIKI_P],
        ),
        q(
            "cube.solver.count",
            "要点",
            "固定 DBL 不动后，2 阶魔方有多少种可到达的状态？",
            "3 674 160 种，即 7!×3⁶",
            ["5 040 种，只算了 7 个角的排列", "40 320 种，那是 8! 全排列", "88 179 840 种，未固定 DBL 时的量级"],
            A("cube.solver.count"),
            "7! = 5040，朝向 3⁶ = 729，5040×729 = 3 674 160。"
            "5040 只是排列；40320 是 8!；八千多万则未固定 DBL 时的量级。",
            [WIKI_P],
        ),
        q(
            "cube.solver.normalize",
            "难点",
            "为什么求解之前要先摆正？",
            "因为前三章解法以 DBL 在左下后为前提，而输入姿势里它可能在任意位",
            [
                "因为摆正之后展开图在屏幕上的观感会整齐许多，便于人工核对",
                "因为涂色输入控件在实现上只肯接受白下绿前这一种固定姿势",
                "因为摆正这一步本身就能把后续求解所需的步数明显缩短",
            ],
            A("cube.solver.normalize"),
            "U/R/F 不碰 DBL 才成立。输入姿势下 DBL 可能在任意位，故先整体转正。"
            "观感、控件限制、缩短步数都不是摆正的真正理由。",
            [SELF("第 6 章 · normalize")],
        ),
        q(
            "cube.solver.frame",
            "考点",
            "摆正姿势下要转 U 面，在你手里（输入姿势）的魔方上，转的是哪个面？",
            "输入姿势里，和摆正后 U 位置对应的那个面",
            [
                "一定还是原来的 U 面，不会因为摆正而换面",
                "一定变成 D 面，因为摆正总是把原来的上翻到下",
                "随机选一个面，只要转向与摆正序列里的 U 相同即可",
            ],
            A("cube.solver.frame"),
            "摆正是整体旋转。to_input_frame 查面对应表换面，转向不变。"
            "「永远仍是 U」「永远变 D」「随机选面」都不对。",
            [SELF("第 6 章 · to_input_frame")],
        ),
        q(
            "cube.solver.predict-f",
            "重点",
            "从复原态做一步 F 之后，R 面展开图四格的颜色（左上→右上→左下→右下）是？",
            "黄、橙、黄、橙",
            ["橙、橙、橙、橙", "绿、绿、绿、绿", "白、橙、白、橙"],
            A("cube.solver.predict-f"),
            "F 把 U 前排黄贴纸转到 R 上排两侧方位。实算 R 面为黄橙黄橙。"
            "全橙是复原 R；全绿是把 F 面看成了 R；白橙则把 D 面贴纸误迁过来。",
            [SELF("第 2 章转动；第 6 章状态")],
            figure=cube_fig("起点", "复原态", setup=""),
            reveal=cube_fig("走一遍", "只做 F", setup="", moves="F", marks=[4, 5, 6, 7]),
        ),
        q(
            "cube.solver.disc-diagnose-normalize",
            "难点",
            "diagnose 和 normalize 各自挡住哪类问题？",
            "diagnose 拒绝非法涂色；normalize 把任意姿势转到 DBL 参照",
            [
                "diagnose 负责把姿势摆正；normalize 负责检查每种颜色是否恰好四格",
                "二者完成的是同一件事，只是历史原因留下了两个不同函数名",
                "diagnose 用来生成均匀随机状态；normalize 负责最短步数求解",
            ],
            A("cube.solver.disc-diagnose-normalize"),
            "先合法性（含朝向模 3），再整体旋转到白下绿前且 DBL 就位。"
            "职责对调、当成同义函数、或塞进随机/最短解，都是接口记混。",
            [SELF("第 6 章 · diagnose 与 normalize")],
        ),
        q(
            "cube.solver.recall-pipeline",
            "要点",
            "摆正之后调用的层先法流水线，三个阶段的完成条件依次是什么？",
            "layer_done → top_oriented → is_solved",
            [
                "is_solved → top_oriented → layer_done",
                "top_oriented → layer_done → is_solved",
                "layer_done → is_solved → top_oriented",
            ],
            A("cube.solver.recall-pipeline"),
            "第 3–5 章：先第一层，再翻顶面，最后换位到整体复原。"
            "其它排列都是把阶段次序记反了。",
            [SELF("第 3–5 章阶段；第 6 章求解入口")],
        ),
    ],
    "07-optimal": [
        q(
            "cube.optimal.table",
            "重点",
            "从复原态做一次广度优先，为什么就能求解所有状态？",
            "因为它把每个可达状态离复原的最少步数都写进了一张完整距离表",
            [
                "因为它靠反复随机试探，在足够多次后就能穷尽全部解法",
                "因为它把人类选手常用的公式全集录进表里供对照查阅",
                "因为固定 DBL 后状态极少，求解时根本不必再做任何搜索",
            ],
            A("cube.optimal.table"),
            "表中距离即最少步数。每步选使距离减 1 的转法，走到 0 就是最短解。"
            "随机试探、公式全集、或以为状态少到不用搜，都不是建表的理由。",
            [SELF("第 7 章 · 反过来搜")],
        ),
        q(
            "cube.optimal.god",
            "重点",
            "2 阶魔方的任何状态，最多几步（半转算一步）就能复原？",
            "11 步",
            ["7 步", "9 步", "14 步"],
            A("cube.optimal.god"),
            "半转度量是 11；只许 90° 转动则是 14。本章距离表最远层是 11。"
            "7/9 偏短；14 是另一度量，不能和半转混用。",
            [WIKI_P],
        ),
        q(
            "cube.optimal.byte",
            "要点",
            "为什么每个状态只需要一个字节来存距离？",
            "因为距离最大只有 11，远小于 255",
            [
                "因为字节恰好是所用语言里最小的整数存储单位",
                "因为状态编号本身已经把距离编码进了下标高位",
                "因为表里其实只需要保存距离的奇偶性这一个比特",
            ],
            A("cube.optimal.byte"),
            "一字节可存 0..255。距离≤11，故 3 674 160 状态约 3.5 MB。"
            "最小整数类型、编号暗含距离、只存奇偶，都不是选用一字节的原因。",
            [SELF("第 7 章 · 表的大小")],
        ),
        q(
            "cube.optimal.descent",
            "难点",
            "有了距离表，求解时每一步怎么选转法？",
            "选一个让距离减 1 的转法",
            [
                "在合法转法里随机挑选一个继续往下走",
                "优先选择同时转动面数最多的那一种转法",
                "按层先法当前所处阶段来决定下一步转法",
            ],
            A("cube.optimal.descent"),
            "距离是几就走几步；每步减 1，到 0 即复原。"
            "随机、最多面、层先阶段，都不是查表下降的选法。",
            [SELF("第 7 章 · 查表求解")],
        ),
        q(
            "cube.optimal.predict-ur",
            "重点",
            "从复原态做 U R 之后，F 面左上那一格（展开图 F 面第 0 格）是什么颜色？",
            "橙色",
            ["绿色", "黄色", "红色"],
            A("cube.optimal.predict-ur"),
            "U 先把橙转到 F 左上；随后 R 不把该格颜色换掉。实算 slot 8 为橙。"
            "绿是复原 F；黄/红是邻面常见色，心理模拟时容易串。",
            [SELF("第 2 章转动；第 7 章状态")],
            figure=cube_fig("起点", "复原态", setup=""),
            reveal=cube_fig("走一遍", "U 然后 R", setup="", moves="U R", marks=[8]),
        ),
        q(
            "cube.optimal.disc-bfs-vs-layer",
            "难点",
            "层先法平均约 35 步、最短解平均约 8.7 步——二者差在哪里？",
            "层先法按人可讲解的阶段子目标走；最短解按全局距离表逐步下降",
            [
                "层先法每一步局部都更优，只是两次统计用的打乱样本不一样",
                "最短解不允许使用半转记号，所以账面上的步数看起来更短",
                "二者搜索过程其实相同，差别只在一个用 C++、一个用 TypeScript",
            ],
            A("cube.optimal.disc-bfs-vs-layer"),
            "阶段法可讲可证，不保证全局最短；BFS 距离表直接给出最少步数。"
            "不是样本不同、不是禁半转、也不是语言实现差异。",
            [SELF("第 5 章平均步数；第 7 章对比")],
        ),
        q(
            "cube.optimal.recall-count",
            "要点",
            "距离表为什么正好有 3 674 160 个格子？要答对需用到前面哪章的结论？",
            "第 6 章已数清：固定 DBL 后可到达状态数是 7!×3⁶",
            [
                "第 7 章重新枚举了另一套状态空间，格子数碰巧等于该整数",
                "半转度量的上帝之数是 11，对 11 做阶乘就得到这个格子数",
                "贴纸 24 格的全排列截断之后，数值上凑成了这个整数",
            ],
            A("cube.optimal.recall-count"),
            "表的下标空间就是第 6 章的可到达状态集；一状态一字节。"
            "新空间、11!、24! 截断都不是该数字的来源。",
            [SELF("第 6 章状态数；第 7 章建表")],
        ),
    ],
}


def longest_is_correct(choices, answer):
    lens = [len(c) for c in choices]
    return lens[answer] == max(lens) and lens.count(max(lens)) == 1


def within_40(correct: str, other: str) -> bool:
    cl, ol = len(correct), len(other)
    if cl == 0:
        return False
    return abs(ol - cl) / cl <= 0.40 + 1e-9


def main():
    QDIR.mkdir(parents=True, exist_ok=True)
    for ch, qs in CHAPTERS.items():
        path = QDIR / f"{ch}.json"
        path.write_text(json.dumps(qs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        json.loads(path.read_text(encoding="utf-8"))
        print("wrote", path.name, "n=", len(qs))

    answers = Counter()
    total = 0
    long_total = 0
    for ch, qs in CHAPTERS.items():
        long_hits = sum(1 for x in qs if longest_is_correct(x["choices"], x["answer"]))
        long_total += long_hits
        print(f"  longest@{ch}: {long_hits}/{len(qs)} = {long_hits/len(qs):.2f}")
        if long_hits / len(qs) > 1 / 3 + 1e-9:
            raise SystemExit(f"FAIL per-chapter longest {ch}")
        for x in qs:
            answers[x["answer"]] += 1
            total += 1
            cl = len(x["choices"][x["answer"]])
            for i, c in enumerate(x["choices"]):
                if PAREN_RE.search(c):
                    raise SystemExit(f"FAIL paren in choices {x['id']} [{i}]: {c}")
                if i == x["answer"]:
                    continue
                if not within_40(x["choices"][x["answer"]], c):
                    raise SystemExit(
                        f"FAIL length {x['id']} [{i}] correct={cl} other={len(c)} text={c!r}"
                    )

    long_pct = long_total / total
    print(f"LONGEST_TOTAL {long_total}/{total} = {long_pct:.3f}")
    if not (0.20 <= long_pct <= 0.35):
        raise SystemExit(f"FAIL overall longest ratio {long_pct:.3f}")

    print("TOTAL", total)
    for i in range(4):
        pct = 100.0 * answers[i] / total
        print(f"  answer={i}: {answers[i]} ({pct:.1f}%)")
        if not (0.20 <= answers[i] / total <= 0.30):
            raise SystemExit(f"FAIL dist {i}")
    print("ACCEPTANCE_STATS_OK")


if __name__ == "__main__":
    main()
