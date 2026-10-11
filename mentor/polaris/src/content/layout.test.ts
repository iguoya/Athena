import { describe, expect, it } from "vitest";
import { stageRank } from "./catalog";
import { layoutByStage } from "./layout";
import { loadCatalog } from "./load";

const catalog = loadCatalog();
// Map 默认序列化成 {}，比较前先展开。
const plain = (value: unknown) => JSON.stringify(value, (_, v) => (v instanceof Map ? [...v] : v));

describe("分阶段布局", () => {
  for (const map of catalog.maps) {
    describe(map.id, () => {
      const layout = layoutByStage(map);

      it("确定性：同一份内容得到逐字节相同的位置", () => {
        expect(plain(layoutByStage(map))).toBe(plain(layout));
      });

      it("每个节点恰好放一次，且都落在画布内", () => {
        expect(layout.nodes.map((n) => n.id).sort()).toEqual(map.nodes.map((n) => n.id).sort());
        for (const node of layout.nodes) {
          expect(node.x).toBeGreaterThanOrEqual(0);
          expect(node.y).toBeGreaterThanOrEqual(0);
          expect(node.x + node.w).toBeLessThanOrEqual(layout.width);
          expect(node.y + node.h).toBeLessThanOrEqual(layout.height);
        }
      });

      it("同一列里卡片不重叠", () => {
        for (const column of layout.columns) {
          const cards = layout.nodes.filter((n) => n.column === column.index).sort((a, b) => a.y - b.y);
          for (let i = 1; i < cards.length; i++) expect(cards[i].y).toBeGreaterThanOrEqual(cards[i - 1].y + cards[i - 1].h);
        }
      });

      it("阶段是列，自左向右为初级 → 中级 → 资深", () => {
        const stageOfColumn = layout.columns.map((c) => c.stage);
        for (let i = 1; i < stageOfColumn.length; i++) expect(stageRank(stageOfColumn[i])).toBeGreaterThan(stageRank(stageOfColumn[i - 1]));
        for (const node of map.nodes) {
          const placed = layout.byId.get(node.id)!;
          expect(layout.columns[placed.column].stage).toBe(node.stage ?? "senior");
        }
      });

      it("同一阶段内，强先修一定排在被依赖者上方", () => {
        for (const node of map.nodes) {
          for (const requiredId of node.requires ?? []) {
            const required = map.nodes.find((n) => n.id === requiredId)!;
            if (required.stage !== node.stage) continue;
            expect(layout.byId.get(requiredId)!.row).toBeLessThan(layout.byId.get(node.id)!.row);
          }
        }
      });

      it("每条边都有路径和从 1 开始连续的编号", () => {
        expect(layout.edges.map((e) => e.number)).toEqual(map.edges.map((_, i) => i + 1));
        for (const edge of layout.edges) {
          expect(edge.path.startsWith("M ")).toBe(true);
          expect(Number.isFinite(edge.mid.x) && Number.isFinite(edge.mid.y)).toBe(true);
        }
      });
    });
  }
});
