# T-101 术语一致性统计（只读）
import json, os, re, collections

root = 'guide/gtkmm'
cur = json.load(open(f'{root}/content/curriculum.json', encoding='utf-8'))
chapters = [s for s in cur['sections'] if s.get('order') in range(1, 11)]

widget_terms = ['部件', '控件', '小部件', '组件', '窗口部件', '小部件']
packing_terms = ['打包', '装填', '组装', '装箱', '封装', '排布']
sig_handler = ['信号处理器', '信号处理函数', '信号处理程序', '信号处理器（', '处理函数']
zh_all = []          # (章, 页, 块号, zh)
for s in chapters:
    for p in s['pages']:
        f = f"{root}/content/chapters/{s['id']}/{p['id']}.json"
        d = json.load(open(f, encoding='utf-8'))
        for i, b in enumerate(d['blocks']):
            if b.get('zh'):
                zh_all.append((s['id'], p['id'], i, b['zh']))

def dist(terms, label):
    c = collections.Counter()
    pages = collections.defaultdict(set)
    for ch, pg, i, zh in zh_all:
        for t in terms:
            if t in zh:
                c[t] += 1
                pages[t].add(ch)
    parts = [f'{k}={v}（章: {", ".join(sorted(pages[k]))}）' for k, v in c.most_common()]
    print(f'{label}: ' + ', '.join(parts))

dist(widget_terms, 'widget 译法')
dist(packing_terms, 'packing 译法')
dist(sig_handler, 'signal handler 译法')

# heading 的 zh 错位填充：heading 的 zh 与相邻 para 的 en 长度相当且 zh 内容长（>40字）即疑似
print('\n--- heading 带 zh 的情况（前10章）---')
for s in chapters:
    for p in s['pages']:
        f = f"{root}/content/chapters/{s['id']}/{p['id']}.json"
        d = json.load(open(f, encoding='utf-8'))
        for i, b in enumerate(d['blocks']):
            if b.get('type') == 'heading' and b.get('zh'):
                flag = ' <<<疑似段落译文错位' if len(b['zh']) > 25 else ''
                print(f"{s['id']}/{p['id']}[{i}] EN={b['text'][:40]!r} ZH={b['zh'][:40]!r}{flag}")

# 全章 widget 用法交叉表（每章用什么词）
print('\n--- 各章 widget 译法分布 ---')
per_ch = collections.defaultdict(collections.Counter)
for ch, pg, i, zh in zh_all:
    for t in ['部件', '控件', '小部件', '组件']:
        if t in zh:
            per_ch[ch][t] += 1
order_of = {s['id']: s.get('order') for s in chapters}
for ch in sorted(per_ch, key=lambda c: order_of.get(c, 0)):
    print(ch, dict(per_ch[ch]))
