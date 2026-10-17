// 后端命令的 类型化封装。字段与 src-tauri/src/lib.rs 的 DTO 一一对应。

export type RunState = "stopped" | "starting" | "ready";

// 学习生命周期（ADR 0139）。
export type Lifecycle = "active" | "built" | "archived";

export interface AppDto {
  id: string;
  title: string;
  summary: string;
  group: string | null;
  groupIndex: number;
  letter: string;
  accent: string;
  groupColor: string;
  icon: string | null;
  lifecycle: Lifecycle;
  state: RunState;
  pos: [number, number, number];
  orbit: number;
  theta: number;
}

export interface OrbitDto {
  a: number;
  b: number;
  c: number;
  tilt: number;
}

export interface CatalogDto {
  repo: string;
  apps: AppDto[];
  orbits: OrbitDto[];
}

import { invoke } from "@tauri-apps/api/core";

export interface StateRow {
  id: string;
  state: RunState;
}

/** 状态点变了才换新数组；没变返回 null，调用方保持原引用，避免空渲染。 */
export function patchStates<T extends { id: string; state: RunState }>(
  items: T[],
  rows: StateRow[],
): T[] | null {
  const byId = new Map(rows.map((row) => [row.id, row.state]));
  let changed = false;
  const next = items.map((item) => {
    const state = byId.get(item.id);
    if (!state || state === item.state) return item;
    changed = true;
    return { ...item, state };
  });
  return changed ? next : null;
}

export interface RescanResult {
  added: string[];
  removed: string[];
  total: number;
  changed: boolean;
}

export function fetchCatalog(): Promise<CatalogDto> {
  return invoke<CatalogDto>("catalog");
}

export function rescanApps(): Promise<RescanResult> {
  return invoke<RescanResult>("rescan_apps");
}

export function openApp(id: string): Promise<void> {
  return invoke("open_app", { id });
}

export function stopApp(id: string): Promise<void> {
  return invoke("stop_app", { id });
}
