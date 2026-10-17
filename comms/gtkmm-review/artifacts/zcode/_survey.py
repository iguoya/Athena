# T-101 临时勘察脚本（只读，最终随报告一并保留在 artifacts/zcode/ 下）
import json, os

root = 'guide/gtkmm'
cur = json.load(open(f'{root}/content/curriculum.json', encoding='utf-8'))
total = 0
for s in cur['sections']:
    if s.get('order') in range(1, 11):
        nblocks = 0
        print(f"=== order {s['order']} {s['id']} status={s['status']}")
        for p in s['pages']:
            f = f"{root}/content/chapters/{s['id']}/{p['id']}.json"
            if not os.path.exists(f):
                print(f"  {p['id']}: MISSING FILE  page status={p.get('status')}")
                continue
            d = json.load(open(f, encoding='utf-8'))
            blocks = d['blocks']
            text_blocks = [b for b in blocks if b['type'] != 'code']
            zh_missing = sum(1 for b in text_blocks if not b.get('zh'))
            stale = [i for i, b in enumerate(blocks) if b.get('stale')]
            nblocks += len(blocks)
            print(f"  {p['id']}: {len(blocks)} blocks (文字段 {len(text_blocks)}), zh 缺失 {zh_missing}, stale@{stale if stale else '-'}, page status={p.get('status')}")
        total += nblocks
        print(f"  小计 {nblocks} blocks")
print('TOTAL blocks (order 1-10):', total)
