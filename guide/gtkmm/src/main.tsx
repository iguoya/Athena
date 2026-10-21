import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import { AppUpdate } from "@athena/app-update";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
    <AppUpdate />
  </React.StrictMode>,
);
