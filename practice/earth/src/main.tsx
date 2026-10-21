import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "@fontsource-variable/inter";
import "@fontsource/noto-sans-sc";
import "./styles.css";
import { App } from "./App";

import { AppUpdate } from "@athena/app-update";
createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
    <AppUpdate />
  </StrictMode>,
);
