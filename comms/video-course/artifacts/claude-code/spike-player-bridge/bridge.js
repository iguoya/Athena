// 注入到播放器页面：只读时间/状态上报，并暴露 seek/pause/play/setPausePoint 给应用 eval 调用。
(function () {
  if (window.__athenaBridge) return;
  window.__athenaBridge = true;
  const report = (ev, extra) => {
    const v = window.__athenaVideo;
    const inv = window.__TAURI_INTERNALS__ && window.__TAURI_INTERNALS__.invoke;
    if (!inv) return;
    inv("bridge_report", {
      ev,
      t: v ? v.currentTime : -1,
      paused: v ? v.paused : true,
      duration: v && isFinite(v.duration) ? v.duration : 0,
      note: extra || "",
    }).catch(() => {});
  };
  let pausePoint = null;
  let lastT = -1;
  window.__athena = {
    seek: (s) => { window.__athenaVideo.currentTime = s; lastT = s; },
    pause: () => window.__athenaVideo.pause(),
    play: () => { const v = window.__athenaVideo; v.muted = true; return v.play(); },
    setPausePoint: (s) => { pausePoint = s; },
    ping: () => report("ping"),
  };
  const timer = setInterval(() => {
    const v = document.querySelector("video");
    if (!v) return;
    clearInterval(timer);
    window.__athenaVideo = v;
    report("ready", "readyState=" + v.readyState + " hasPlayerApi=" + !!window.player);
    ["play", "pause", "seeked", "ended", "waiting", "stalled"].forEach((e) => v.addEventListener(e, () => report(e, (e === "pause" ? "TEXT=" + document.body.innerText.replace(/\s+/g, " ").slice(0, 200) + " | UA=" + navigator.userAgent.slice(-40) + " " : "") + "vis=" + document.visibilityState + " focus=" + document.hasFocus() + " rs=" + v.readyState + " ui=" + (document.querySelector(".bpx-player-toast-text,.bpx-player-login-tip,.bili-mini-mask") ? "popup" : "none"))));
    setInterval(() => {
      const t = v.currentTime;
      // 暂停点：自然播放跨过该点才触发；拖进度条越过（一次跳变超过 1.5 秒）按「已过」处理，不触发。
      if (pausePoint !== null && !v.paused && lastT >= 0 && lastT < pausePoint && t >= pausePoint && t - lastT < 1.5) {
        v.pause();
        report("pausepoint", "at=" + pausePoint);
        pausePoint = null;
      }
      lastT = t;
      if (!v.paused) report("tick");
    }, 100);
  }, 200);
})();
