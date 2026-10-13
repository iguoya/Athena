import * as THREE from "three";

/** 大气标尺方向（世界坐标系，不随地球倾斜与自转）：剖面盘 B 与全球模式的共用方向。
    大气标尺接近水平——竖着伸的话 35786 km 的锚点会把标签顶出窗口外。 */
export const ATMOS_RULER_DIR = new THREE.Vector3(-0.93, 0.34, 0).normalize();

export interface ViewFocus {
  /** 相机最终看向的点（场景单位） */
  target: [number, number, number];
  /** 相机到该点的距离（场景单位） */
  distance: number;
  /** 相机相对目标的方向（场景坐标，不必归一化）；缺省沿当前视线方向 */
  lookFrom?: [number, number, number];
}

/** 默认视图「地面视角·观空中」：贴近地表低角度看大气标尺——地球占画面下方，
    大气各层的界环从地平线向上展开，居民锚点沿标尺排开。空中分层优先，
    地球内部（剖面）不进第一眼。 */
export const GROUND_VIEW_FOCUS: ViewFocus = {
  target: [ATMOS_RULER_DIR.x * 1.01, ATMOS_RULER_DIR.y * 1.01, ATMOS_RULER_DIR.z * 1.01],
  distance: 0.35,
  lookFrom: [0.1, 0.22, -0.97],
};

/** 全球全貌：看整个地球（含外逸层渐隐包络） */
export const GLOBAL_VIEW_FOCUS: ViewFocus = {
  target: [0, 0, 0],
  distance: 3.4,
};
