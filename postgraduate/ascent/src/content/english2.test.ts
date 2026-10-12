import { describe, expect, it } from "vitest";
import { curriculum, english2, trackItems } from "./english2";
import { sources } from "./index";

const pathsOf = () =>
  curriculum.stages.flatMap((s) => s.tracks.flatMap((t) => [...(t.decks ?? (t.deck ? [t.deck] : [])), t.assessment]));

describe("考研英语二内容", () => {
  it("课表里每条轨的题库、考核与短文都能找到", () => {
    for (const stage of curriculum.stages) {
      for (const track of stage.tracks) {
        for (const path of [...(track.decks ?? (track.deck ? [track.deck] : [])), track.assessment])
          expect(english2.deck(path), `${track.id} → ${path}`).toBeDefined();
        if (track.passage) expect(english2.passage(track.passage), track.passage).toBeTruthy();
      }
    }
    expect(trackItems(english2, curriculum.stages[0].tracks[0]).length).toBeGreaterThan(0);
  });

  it("迁过来的 617 题全部打包（ADR 0026 不分流）", () => {
    const total = [...new Set(pathsOf())].reduce((n, path) => n + (english2.deck(path)?.items.length ?? 0), 0);
    expect(total).toBe(617);
  });

  it("每道题都有出处，且出处登记过", () => {
    for (const path of pathsOf()) {
      const d = english2.deck(path);
      for (const item of d?.items ?? []) {
        const refs = item.source?.length ? item.source : (d?.source ?? []);
        expect(refs.length, `${path} ${item.id}`).toBeGreaterThan(0);
        for (const ref of refs) expect(sources[ref.source_id], `${item.id} → ${ref.source_id}`).toBeDefined();
      }
    }
  });
});
