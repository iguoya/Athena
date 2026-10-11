import { Canvas } from "@react-three/fiber";
import type { ReactNode } from "react";

/**
 * 真实比例的深度跨度（贴地公里级到地球静止轨道 5.6 R）用默认深度缓冲必然
 * z-fighting，必须开对数深度缓冲（ADR 0128 决策 5）；far 留到 30 R，别让
 * 远处的锚点被裁掉。
 */
export function EarthCanvas({ children }: { children: ReactNode }) {
  return (
    <Canvas
      gl={{ logarithmicDepthBuffer: true, antialias: true }}
      camera={{ fov: 40, near: 0.002, far: 30, position: [2.7, 1.6, 2.7] }}
      onCreated={({ gl }) => {
        gl.localClippingEnabled = true;
      }}
      dpr={[1, 2]}
    >
      {children}
    </Canvas>
  );
}
