import type { ComponentType } from "react";
import { BaseConverter } from "./base-converter";
import { ComplementExplorer } from "./complement-explorer";
import { PipelineSim } from "./pipeline-sim";
import { ProcessStates } from "./process-states";
import { SemaphoreAnim } from "./semaphore-anim";
import { ScheduleGantt } from "./schedule-gantt";
import { PageReplacement } from "./page-replacement";

/** viz 块的组件注册表:内容 JSON 用 component 名引用,这里认路。 */
export const VizRegistry: Record<string, ComponentType<{ params: Record<string, unknown> }>> = {
  "base-converter": BaseConverter,
  "complement-explorer": ComplementExplorer,
  "pipeline-sim": PipelineSim,
  "process-states": ProcessStates,
  "semaphore-anim": SemaphoreAnim,
  "schedule-gantt": ScheduleGantt,
  "page-replacement": PageReplacement,
} as unknown as Record<string, ComponentType<{ params: Record<string, unknown> }>>;
