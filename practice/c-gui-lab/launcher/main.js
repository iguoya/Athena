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

// 两种布局：开发树 exe 在 build/apps/，运行期 DLL 靠本机 MSYS2；安装布局
// （electron-builder）里 exe 与收好的 MinGW 运行库 DLL 在 resources/native/ 下，
// 不假设装机装过 MSYS2。exe 不能从 asar 里 spawn，所以原生程序不进 asar——
// 选 extraResources 而不是 asarUnpack：后者得把 build/ 连中间产物一起收进 asar
// 再逐项解出，extraResources 直接按白名单把干净的运行时子集放 resources/native，
// 目录结构自定，asar 的打包规则碰不到它。
const NATIVE_ROOT = app.isPackaged
  ? path.join(process.resourcesPath, "native")
  : path.join(PROJECT_ROOT, "build", "apps");
const LAYOUT_ROOT = app.isPackaged ? process.resourcesPath : PROJECT_ROOT;

// 自研样式程序：CMake 产物。bin 相对 NATIVE_ROOT；args 用于同一 exe 的不同形态
// （如 LVGL 官方 demo）。
const APPS = {
  gtk: {
    title: "GTK4 + Adwaita + CSS",
    bin: path.join("gtk-style", "gtk-style.exe"),
  },
  imgui: {
    title: "Dear ImGui",
    bin: path.join("imgui-style", "imgui-style.exe"),
  },
  "imgui-demo": {
    title: "ImGui ShowDemoWindow()",
    bin: path.join("imgui-style", "imgui-style.exe"),
    args: ["--demo"],
  },
  lvgl: {
    title: "LVGL + SDL2",
    bin: path.join("lvgl-style", "lvgl-style.exe"),
  },
  "lvgl-demo": {
    title: "LVGL 官方 widgets 合集",
    bin: path.join("lvgl-style", "lvgl-style.exe"),
    args: ["--demo"],
  },
  raygui: {
    title: "raygui 控件套件",
    bin: path.join("raygui-demo", "raygui-demo.exe"),
  },
  nuklear: {
    title: "Nuklear 演示",
    bin: path.join("nuklear-demo", "nuklear-demo.exe"),
  },
  "nuklear-gdi": {
    title: "Nuklear GDI 原生",
    bin: path.join("nuklear-gdi-demo", "nuklear-gdi-demo.exe"),
  },
  microui: {
    title: "microui 演示",
    bin: path.join("microui-demo", "microui-demo.exe"),
  },
};

function appExe(conf) {
  return path.join(NATIVE_ROOT, conf.bin);
}

// 官方 demo：随 MSYS2 安装，探测到才给入口。安装机上通常没有 MSYS2，全部灰掉
// 是预期降级，不把官方 demo 打进安装包。
const OFFICIAL = {
  "gtk4-demo": path.join(MSYS2_BIN, "gtk4-demo.exe"),
  "gtk4-widget-factory": path.join(MSYS2_BIN, "gtk4-widget-factory.exe"),
  "gtk4-node-editor": path.join(MSYS2_BIN, "gtk4-node-editor.exe"),
  "adwaita-1-demo": path.join(MSYS2_BIN, "adwaita-1-demo.exe"),
};

// 开发树：GTK / SDL 的运行时 DLL 都在 MSYS2 的 bin 里，spawn 时注入 PATH。
// 安装布局：DLL 已收在各 exe 旁边，Windows 加载 DLL 时先查应用程序自己的
// 目录，不需要也不应该再依赖 PATH 里的 MSYS2。
function childEnv() {
  if (app.isPackaged) return { ...process.env };
  return {
    ...process.env,
    PATH: `${MSYS2_BIN};${process.env.PATH || process.env.Path || ""}`,
  };
}

const running = new Map(); // key -> ChildProcess

function launch(key) {
  const conf = APPS[key];
  if (!conf) return { ok: false, message: `未知程序：${key}` };
  const exe = appExe(conf);
  if (!fs.existsSync(exe))
    return { ok: false, message: `尚未编译：${path.relative(LAYOUT_ROOT, exe)}` };
  if (running.has(key) && running.get(key).exitCode === null)
    return { ok: false, message: `${conf.title} 已在运行（窗口可能被挡住了）` };

  try {
    const child = spawn(exe, conf.args || [], {
      cwd: path.dirname(exe),
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
    result.apps[key] = fs.existsSync(appExe(conf));
  for (const [name, exe] of Object.entries(OFFICIAL))
    result.official[name] = fs.existsSync(exe);
  return result;
}

ipcMain.handle("lab:launch", (_ev, key) => launch(key));
ipcMain.handle("lab:launch-demo-window", () => launch("imgui-demo"));ipcMain.handle("lab:launch-official", (_ev, name) => launchOfficial(name));
ipcMain.handle("lab:probe", () => probe());

function createWindow() {
  const win = new BrowserWindow({
    width: 1400,
    height: 920,
    backgroundColor: "#f5f6f8", // 与 renderer.css 的亮色主题一致，避免启动闪暗
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

// 无人值守自测：npx electron . --selftest —— 验证 probe 与 spawn 链路。
// 安装布局下这就是「装得出、跑得起」的真验证：七个 exe 都在、每个都能起进程。
if (process.argv.includes("--selftest")) {
  app.whenReady().then(async () => {
    console.log(
      "layout:",
      `${app.isPackaged ? "packaged" : "dev"} native=${NATIVE_ROOT}`,
    );
    console.log("probe:", JSON.stringify(probe()));

    // 同一 exe 的 --demo 形态不重复起；每个唯一 exe：spawn → 4 秒后仍存活
    // 即算跑起来 → 杀掉（DLL 没收齐时 Windows 可能弹「缺 DLL」对话框让进程
    // 挂着存活，这层误判在打包作业里用 ntldd 复查兜住）。
    const failures = [];
    const seen = new Set();
    for (const [key, conf] of Object.entries(APPS)) {
      const exe = appExe(conf);
      if (!fs.existsSync(exe)) {
        failures.push(`${key}: 缺 ${exe}`);
        continue;
      }
      if (seen.has(exe)) continue;
      seen.add(exe);
      try {
        const child = spawn(exe, conf.args || [], {
          cwd: path.dirname(exe),
          env: childEnv(),
          detached: true,
          stdio: "ignore",
        });
        let spawnError = null; // ENOENT 之类只在 error 事件里出现，不抛异常
        child.on("error", (err) => {
          spawnError = err;
        });
        await new Promise((res) => setTimeout(res, 4000));
        const alive = !spawnError && child.exitCode === null && child.signalCode === null;
        console.log(`spawn ${key}:`, alive ? "alive" : `exited (code ${child.exitCode})`);
        if (!alive) failures.push(`${key}: 进程 4 秒内退出`);
        child.kill();
        await new Promise((res) => setTimeout(res, 300));
      } catch (err) {
        failures.push(`${key}: ${err.message}`);
      }
    }
    if (failures.length) {
      console.error("SELFTEST-FAIL:", failures.join("; "));
      app.quit();
      process.exit(1);
    }
    console.log("SELFTEST-OK");
    app.quit();
    process.exit(0);
  });
} else {
  app.whenReady().then(createWindow);
}
app.on("window-all-closed", () => app.quit());
