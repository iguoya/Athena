import { AppUpdate } from "@athena/app-update";
import React, { Suspense, lazy } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

/** maplibre 约 1MB：先画壳，再动态拉地图应用（P5） */
const App = lazy(() => import("./App"));

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <Suspense
      fallback={
        <div
          style={{
            display: "grid",
            placeItems: "center",
            height: "100vh",
            fontFamily: "Songti SC, Noto Serif SC, serif",
            color: "#6b5e4e",
            background: "#f3efe6",
          }}
        >
          <div style={{ textAlign: "center" }}>
            <p style={{ letterSpacing: "0.35em", fontSize: 12 }}>JIUZHOU</p>
            <p style={{ fontSize: 28, color: "#9a3412", marginTop: 8 }}>九州</p>
            <p style={{ fontSize: 13, marginTop: 12 }}>载入地图…</p>
          </div>
        </div>
      }
    >
      <App />
      <AppUpdate />
    </Suspense>
  </React.StrictMode>,
);
