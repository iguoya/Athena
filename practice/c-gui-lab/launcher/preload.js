const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("lab", {
  launch: (key) => ipcRenderer.invoke("lab:launch", key),
  launchDemoWindow: () => ipcRenderer.invoke("lab:launch-demo-window"),
  launchOfficial: (name) => ipcRenderer.invoke("lab:launch-official", name),
  probe: () => ipcRenderer.invoke("lab:probe"),
});
