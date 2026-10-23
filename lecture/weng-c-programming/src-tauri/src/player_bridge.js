// 注入到 B 站视频页（ADR 0182 决策 3、ADR 0183）：只读上报播放状态，并暴露 seek/pause/play/setPausePoint 给应用 eval 调用。
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
  let playIssued = false;
  let lastT = -1;
  window.__athena = {
    seek: (s) => { if (window.__athenaVideo) { window.__athenaVideo.currentTime = s; lastT = s; } },
    pause: () => window.__athenaVideo && window.__athenaVideo.pause(),
    // 先静音再播放：页面没有用户手势时，带声音的 play() 会被自动播放策略拦下；用户可在播放器里自己取消静音。
    play: () => { const v = window.__athenaVideo; if (!v) return; playIssued = true; v.muted = true; return v.play(); },
    setPausePoint: (s) => { pausePoint = s; },
    ping: () => report("ping"),
  };
  const timer = setInterval(() => {
    const v = document.querySelector(".bpx-player-video-wrap video") || document.querySelector("video");
    if (!v) return;
    clearInterval(timer);
    window.__athenaVideo = v;
    // 页面加载后会自己开始播放：先暂停，等课堂区发令。页面可能晚几秒才起播，所以在「课堂区还没发过播放令」的前 8 秒里盯着。
    const guard = setInterval(() => { if (!playIssued && !v.paused) v.pause(); }, 200);
    setTimeout(() => clearInterval(guard), 8000);
    // 网页全屏：用站点自己的按钮让播放器占满窗格，推荐、评论等页面其余部分自然不在视野里（不改页面内容）。
    // 控制条可能比 <video> 晚几秒才渲染出来，所以等按钮出现后点一次就停（再点会切回去）。
    const webTimer = setInterval(() => {
      const web = document.querySelector(".bpx-player-ctrl-web");
      if (web) { web.click(); clearInterval(webTimer); }
    }, 500);
    setTimeout(() => clearInterval(webTimer), 15000);
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
