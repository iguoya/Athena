#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from collections import Counter
from pathlib import Path

d = json.loads(Path(__file__).resolve().parent.parent.joinpath("content/atlas.json").read_text(encoding="utf-8"))
print("ERAS:")
for e in d["eras"]:
    print(f"  {e['id']:24} {e['title']:20} {e['from']:6}->{e['to']:6} terr={e.get('territoryId')}")
print("events by era:", dict(Counter(e["eraId"] for e in d["events"])))
print("places", len(d["places"]))
for p in d["places"]:
    print(f"  {p['id']:22} {p['modern']:12} {p['lon']:.2f},{p['lat']:.2f} names={len(p.get('names',[]))}")
