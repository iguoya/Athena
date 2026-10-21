import { AppUpdate } from "@athena/app-update";
import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import "./styles.css";

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
    <AppUpdate />
  </React.StrictMode>,
);
