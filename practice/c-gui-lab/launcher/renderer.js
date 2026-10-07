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
    if (!ready && btn)
      btn.disabled = true;
  }
  const anyReady = Object.values(probe.apps).some(Boolean);
  if (!anyReady)
    setStatus("三个原生程序尚未编译：先跑 cmake --preset ucrt64 && cmake --build --preset ucrt64", "err");

  // GTK 生态官方演示程序：MSYS2 里有才亮
  for (const [name, exists] of Object.entries(probe.official)) {
    const btn = document.querySelector(`[data-official="${name}"]`);
    if (btn)
      btn.disabled = !exists;
  }
}

document.querySelectorAll("[data-launch]").forEach((btn) =>
  btn.addEventListener("click", async () => {
    const res = await window.lab.launch(btn.dataset.launch);
    setStatus(res.message, res.ok ? "ok" : "err");
  })
);

document.querySelectorAll("[data-official]").forEach((btn) =>
  btn.addEventListener("click", async () => {
    const res = await window.lab.launchOfficial(btn.dataset.official);
    setStatus(res.message, res.ok ? "ok" : "err");
  })
);

boot();
