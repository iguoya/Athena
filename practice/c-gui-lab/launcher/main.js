// Electron 母体：画廊界面 + 拉起三个原生样式程序与两个官方 demo。
//
// 原生程序被 spawn 成独立进程（detached），母体退出后它们继续运行——
// 对比观感时通常想留下窗口慢慢看。

const { app, BrowserWindow, ipcMain } = require("electron");
const { spawn } = require("child_process");
const path = require("path");
const fs = require("fs");

const MSYS2_BIN = "C:\\msys64\\ucrt64\\bin";
const PROJECT_ROOT = path.join(__dirname, "..");

// 自研样式程序：CMake 产物
const APPS = {
  gtk: {
    title: "GTK4 + Adwaita + CSS",
    exe: path.join(PROJECT_ROOT, "build", "apps", "gtk-style", "gtk-style.exe"),
  },
  imgui: {
    title: "Dear ImGui",
    exe: path.join(PROJECT_ROOT, "build", "apps", "imgui-style", "imgui-style.exe"),
  },
  lvgl: {
    title: "LVGL + SDL2",
    exe: path.join(PROJECT_ROOT, "build", "apps", "lvgl-style", "lvgl-style.exe"),
  },
};

// 官方 demo：随 MSYS2 安装，探测到才给入口
const OFFICIAL = {
  "gtk4-demo": path.join(MSYS2_BIN, "gtk4-demo.exe"),
  "adwaita-1-demo": path.join(MSYS2_BIN, "adwaita-1-demo.exe"),
};

// GTK / SDL 的运行时 DLL 都在 MSYS2 的 bin 里，spawn 时注入 PATH
function childEnv() {
  return {
    ...process.env,
    PATH: `${MSYS2_BIN};${process.env.PATH || process.env.Path || ""}`,
  };
}

const running = new Map(); // key -> ChildProcess

function launch(key, args = []) {
  const conf = APPS[key];
  if (!conf) return { ok: false, message: `未知程序：${key}` };
  if (!fs.existsSync(conf.exe))
    return { ok: false, message: `尚未编译：${path.relative(PROJECT_ROOT, conf.exe)}` };
  if (running.has(key) && running.get(key).exitCode === null)
    return { ok: false, message: `${conf.title} 已在运行（窗口可能被挡住了）` };

  try {
    const child = spawn(conf.exe, args, {
      cwd: path.dirname(conf.exe),
      env: childEnv(),
      detached: true,
      stdio: "ignore",
    });
    child.on("exit", (code) => running.delete(key));
    child.unref();
    running.set(key, child);
    return { ok: true, message: `${conf.title} 已启动（PID ${child.pid}）` };
  } catch (err) {
    return { ok: false, message: `启动失败：${err.message}` };
  }
}

function launchOfficial(name) {
  const exe = OFFICIAL[name];
  if (!exe || !fs.existsSync(exe))
    return { ok: false, message: `未检测到 ${name}（需要 MSYS2 安装对应包）` };
  try {
    const child = spawn(exe, [], { cwd: MSYS2_BIN, env: childEnv(), detached: true, stdio: "ignore" });
    child.unref();
    return { ok: true, message: `${name} 已启动（PID ${child.pid}）` };
  } catch (err) {
    return { ok: false, message: `启动失败：${err.message}` };
  }
}

function probe() {
  const result = { apps: {}, official: {} };
  for (const [key, conf] of Object.entries(APPS))
    result.apps[key] = fs.existsSync(conf.exe);
  for (const [name, exe] of Object.entries(OFFICIAL))
    result.official[name] = fs.existsSync(exe);
  return result;
}

ipcMain.handle("lab:launch", (_ev, key) => launch(key));
ipcMain.handle("lab:launch-demo-window", () => launch("imgui", ["--demo"]));
ipcMain.handle("lab:launch-official", (_ev, name) => launchOfficial(name));
ipcMain.handle("lab:probe", () => probe());

function createWindow() {
  const win = new BrowserWindow({
    width: 1400,
    height: 920,
    backgroundColor: "#0e0f13",
    title: "C GUI Lab",
    autoHideMenuBar: true,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });
  win.loadFile(path.join(__dirname, "index.html"));

  // 自动化截图：npx electron . --shot=path（渲染层自捕获，不受前台锁定影响）
  const shotArg = process.argv.find((a) => a.startsWith("--shot="));
  if (shotArg) {
    win.webContents.once("did-finish-load", async () => {
      await new Promise((r) => setTimeout(r, 1500)); // 等 renderer 的 probe 刷新按钮状态
      const img = await win.webContents.capturePage();
      fs.writeFileSync(shotArg.slice("--shot=".length), img.toPNG());
      console.log("SHOT-SAVED");
      app.quit();
    });
  }
}

// 无人值守自测：npx electron . --selftest —— 验证 probe 与 spawn 链路
if (process.argv.includes("--selftest")) {
  app.whenReady().then(async () => {
    console.log("probe:", JSON.stringify(probe()));
    const r = launch("gtk");
    console.log("launch gtk:", JSON.stringify(r));
    await new Promise((res) => setTimeout(res, 4000));
    const alive = running.has("gtk") && running.get("gtk").exitCode === null;
    console.log("gtk alive after 4s:", alive);
    app.quit();
    process.exit(alive ? 0 : 1);
  });
} else {
  app.whenReady().then(createWindow);
}
app.on("window-all-closed", () => app.quit());
