# T-102 导出第 11–21 章英中对照文本（只读），输出到 artifacts/zcode/dump/
import json, os

root = 'guide/gtkmm'
out_dir = 'comms/gtkmm-review/artifacts/zcode/dump'
os.makedirs(out_dir, exist_ok=True)
cur = json.load(open(f'{root}/content/curriculum.json', encoding='utf-8'))

def plain(b):
    # 快照段的英文文本字段名可能是 en / text，兼容两种
    for k in ('en', 'text', 'src'):
        if k in b:
            return b[k]
    return json.dumps({k: v for k, v in b.items() if k not in ('zh', 'sha', 'fingerprint')}, ensure_ascii=False)

missing_pages = []
for s in cur['sections']:
    if s.get('order') not in range(11, 22):
        continue
    lines = []
    for p in s['pages']:
        f = f"{root}/content/chapters/{s['id']}/{p['id']}.json"
        if not os.path.exists(f):
            missing_pages.append(f)
            continue
        d = json.load(open(f, encoding='utf-8'))
        lines.append(f"### 页 {p['id']}  (page status={p.get('status')})")
        for i, b in enumerate(d['blocks']):
            t = b.get('type')
            if t == 'code':
                lines.append(f"[{i}] CODE file={b.get('file','')} {len(b.get('text','') or b.get('en','') or '')} chars")
                continue
            zh = b.get('zh', '')
            tag = '' if zh else '  <<<ZH缺失>>>'
            st = b.get('stale', False)
            sttag = '  <<<STALE>>>' if st else ''
            lines.append(f"[{i}] {t}{tag}{sttag}")
            lines.append(f"  EN: {plain(b)}")
            lines.append(f"  ZH: {zh if zh else '(无)'}")
            lines.append('')
    out = f"{out_dir}/{s['order']:02d}-{s['id']}.txt"
    open(out, 'w', encoding='utf-8').write('\n'.join(lines))
    print(out, len(lines), 'lines')

print('missing pages:', missing_pages)
