import type { ComponentType } from "react";
import ProcessStates from "./ProcessStates";

export type VizProps = { params: Record<string, unknown> };

/** viz 块的组件注册表:内容 JSON 用 component 名引用,这里认路(check.py 会对账)。 */
export const VizRegistry: Record<string, ComponentType<VizProps>> = {
  "process-states": ProcessStates,
};

export function resolveViz(name: string): ComponentType<VizProps> | null {
  return VizRegistry[name] ?? null;
}
