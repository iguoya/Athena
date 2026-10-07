const statusEl = document.getElementById("status");

function setStatus(text, kind = "") {
  statusEl.textContent = text;
  statusEl.className = `status ${kind}`;
}

async function boot() {
  const probe = await window.lab.probe();

  // 三个自研程序：已编译才亮
  for (const [key, ready] of Object.entries(probe.apps)) {
    const btn = document.querySelector(`[data-launch="${key}"]`);
    if (!ready)
      btn.disabled = true;
  }
  const anyReady = Object.values(probe.apps).some(Boolean);
  if (!anyReady)
    setStatus("三个原生程序尚未编译：先跑 cmake --preset ucrt64 && cmake --build --preset ucrt64", "err");

  // 官方 demo：MSYS2 里有才亮
  document.getElementById("btn-gtk-demo").disabled = !probe.official["gtk4-demo"];
  document.getElementById("btn-adw-demo").disabled = !probe.official["adwaita-1-demo"];
}

document.querySelectorAll("[data-launch]").forEach((btn) =>
  btn.addEventListener("click", async () => {
    const res = await window.lab.launch(btn.dataset.launch);
    setStatus(res.message, res.ok ? "ok" : "err");
  })
);

document.getElementById("btn-imgui-demo").addEventListener("click", async () => {
  const res = await window.lab.launchDemoWindow();
  setStatus(res.message, res.ok ? "ok" : "err");
});

document.querySelectorAll("[data-official]").forEach((btn) =>
  btn.addEventListener("click", async () => {
    const res = await window.lab.launchOfficial(btn.dataset.official);
    setStatus(res.message, res.ok ? "ok" : "err");
  })
);

boot();
