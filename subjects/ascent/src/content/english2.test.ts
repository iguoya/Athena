import { describe, expect, it } from "vitest";
import { curriculum, english2From, mergeDeck, missingCount, privateIndex, trackItems, type Deck } from "./english2";
import { sources } from "./index";

const deck = (ids: string[]): Deck => ({
  topic_id: "t",
  kind: "vocab",
  items: ids.map((id) => ({ id, prompt: id })),
});

describe("考研英语二内容", () => {
  it("合并时按拆分前的原始顺序排回去", () => {
    const index = { files: { "a.json": { private: ["p1", "p2"], order: ["x", "p1", "y", "p2"] } } };
    const merged = mergeDeck("a.json", deck(["x", "y"]), deck(["p1", "p2"]), index);
    expect(merged?.items.map((i) => i.id)).toEqual(["x", "p1", "y", "p2"]);
  });

  it("只有一边时原样返回，两边都没有时是 undefined", () => {
    expect(mergeDeck("b.json", deck(["x"]), undefined)?.items.map((i) => i.id)).toEqual(["x"]);
    expect(mergeDeck("b.json", undefined, undefined)).toBeUndefined();
  });

  it("本机没有资料时如实报出缺的题数", () => {
    const total = Object.values(privateIndex.files).reduce((n, f) => n + f.private.length, 0);
    expect(total).toBeGreaterThan(0);
    expect(missingCount({ decks: {}, passages: {} })).toBe(total);
  });

  it("课表里每条轨的题库与考核都能找到（公开部分或本机清单里有）", () => {
    const content = english2From({ decks: {}, passages: {} });
    for (const stage of curriculum.stages) {
      for (const track of stage.tracks) {
        const paths = [...(track.decks ?? (track.deck ? [track.deck] : [])), track.assessment];
        for (const path of paths) {
          const known = content.deck(path) !== undefined || path in privateIndex.files;
          expect(known, `${track.id} → ${path}`).toBe(true);
        }
        if (track.passage) expect(content.passage(track.passage), track.passage).toBeTruthy();
      }
    }
    expect(trackItems(content, curriculum.stages[0].tracks[0]).length).toBeGreaterThan(0);
  });

  it("公开题库里每道题的出处都登记过，且不引用只能本机用的来源", () => {
    const content = english2From({ decks: {}, passages: {} });
    const paths = curriculum.stages.flatMap((s) =>
      s.tracks.flatMap((t) => [...(t.decks ?? (t.deck ? [t.deck] : [])), t.assessment]),
    );
    for (const path of paths) {
      const d = content.deck(path);
      for (const item of d?.items ?? []) {
        const refs = item.source?.length ? item.source : (d?.source ?? []);
        expect(refs.length, `${path} ${item.id}`).toBeGreaterThan(0);
        for (const ref of refs) {
          expect(sources[ref.source_id], `${item.id} → ${ref.source_id}`).toBeDefined();
          const contentRef = ["verbatim", "quoted", "adapted"].includes(ref.relation);
          expect(contentRef && sources[ref.source_id].kind === "local-only", `${item.id} 公开题引用了本机来源`).toBe(false);
        }
      }
    }
  });
});
