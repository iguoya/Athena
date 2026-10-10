// 后端命令的 类型化封装。字段与 src-tauri/src/lib.rs 的 DTO 一一对应。

export type RunState = "stopped" | "starting" | "ready";

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

export function fetchCatalog(): Promise<CatalogDto> {
  return invoke<CatalogDto>("catalog");
}

export function openApp(id: string): Promise<void> {
  return invoke("open_app", { id });
}

export function stopApp(id: string): Promise<void> {
  return invoke("stop_app", { id });
}
