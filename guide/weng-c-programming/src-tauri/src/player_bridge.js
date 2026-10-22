// 注入到 B 站外链播放器页面（ADR 0182 决策 3）：只读上报播放状态，并暴露 seek/pause/play/setPausePoint 给应用 eval 调用。
// 只用标准 <video> 元素，不依赖 B 站私有 API；不下载、不抓取、不改页面内容。
(function () {
  if (window.__athenaBridge) return;
  window.__athenaBridge = true;
  const inv = () => window.__TAURI_INTERNALS__ && window.__TAURI_INTERNALS__.invoke;
  const report = (ev, note) => {
    const v = window.__athenaVideo;
    const call = inv();
    if (!call) return;
    call("bridge_report", {
      ev,
      t: v ? v.currentTime : -1,
      paused: v ? v.paused : true,
      duration: v && isFinite(v.duration) ? v.duration : 0,
      note: note || "",
    }).catch(() => {});
  };
  let pausePoint = null;
  let lastT = -1;
  window.__athena = {
    seek: (s) => { if (window.__athenaVideo) { window.__athenaVideo.currentTime = s; lastT = s; } },
    pause: () => window.__athenaVideo && window.__athenaVideo.pause(),
    // 先静音再播放：页面没有用户手势时，带声音的 play() 会被自动播放策略拦下；用户可在播放器里自己取消静音。
    play: () => { const v = window.__athenaVideo; if (!v) return; v.muted = true; return v.play(); },
    setPausePoint: (s) => { pausePoint = s; },
    ping: () => report("ping"),
  };
  const timer = setInterval(() => {
    const v = document.querySelector("video");
    if (!v) return;
    clearInterval(timer);
    window.__athenaVideo = v;
    // 页面加载后会自己开始播放（autoplay=0 不生效）：先暂停，等课堂区发令。
    try { v.pause(); } catch (e) { /* 页面还没准备好就算了 */ }
    report("ready");
    ["play", "pause", "seeked", "ended", "waiting"].forEach((e) => v.addEventListener(e, () => report(e)));
    setInterval(() => {
      const t = v.currentTime;
      // 暂停点：自然播放跨过该点才触发；拖进度条越过（一次跳变超过 1.5 秒）按「已过」处理，不触发。
      if (pausePoint !== null && !v.paused && lastT >= 0 && lastT < pausePoint && t >= pausePoint && t - lastT < 1.5) {
        v.pause();
        report("pausepoint", String(pausePoint));
        pausePoint = null;
      }
      lastT = t;
      if (!v.paused) report("tick");
    }, 100);
  }, 200);
})();
