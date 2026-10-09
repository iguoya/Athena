import { markRaw, type Component } from "vue";
import ProcessStates from "./ProcessStates.vue";

/** viz 块的组件注册表:内容 JSON 用 component 名引用,这里认路(check.py 会对账)。 */
export const VizRegistry: Record<string, Component> = {
  "process-states": markRaw(ProcessStates),
};

export function resolveViz(name: string): Component | null {
  return VizRegistry[name] ?? null;
}
