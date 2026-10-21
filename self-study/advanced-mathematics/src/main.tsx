import { mountAppUpdate } from "@athena/app-update/mount";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import "./styles.css";

// 更新器挂载（ADR 0172）：独立于应用界面，自检更新并在同意后重启。
mountAppUpdate();

createRoot(document.getElementById("root")!).render(<App />);
