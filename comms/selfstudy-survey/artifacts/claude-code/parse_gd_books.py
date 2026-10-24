import re, json, sys
lines = open('dl_gd/gd602026.txt', encoding='utf-8').read().split('\n')
start = next(i for i,l in enumerate(lines) if l.startswith('序号 课程代码 课程名称 教材名称'))
rows = []
cur = None
for l in lines[start:]:
    if l.startswith('=== p') or re.fullmatch(r'\d+', l.strip()) or l.startswith('序号 课程代码'):
        continue
    m = re.match(r'^(\d{1,3}) (\d{5}) (.*)$', l)
    if m:
        cur = {'seq': int(m.group(1)), 'code': m.group(2), 'rest': m.group(3)}
        rows.append(cur)
    elif cur is not None:
        cur['rest'] += ' ' + l.strip()
json.dump(rows, open('gd_books_raw.json','w',encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(rows))
need = set('01644 00023 02354 08947 13013 14026 02363 14260 02356 13473 14319 02324 13180 13005 08074 13003 13011 13015 13009 13008 07844 13420 07454 02141 13958 12573 13247 14383 14255 12572 13000 15040 15043 15044 03344 14027'.split())
for r in rows:
    if r['code'] in need:
        print(r['seq'], r['code'], r['rest'])
