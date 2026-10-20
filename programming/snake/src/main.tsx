import React from "react";
import { createRoot } from "react-dom/client";
import "@fontsource/noto-sans-sc/400.css";
import "@fontsource/noto-sans-sc/700.css";
import App from "./App";
import { AppUpdate } from "@athena/app-update";
import "./styles.css";

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
    <AppUpdate />
  </React.StrictMode>,
);
