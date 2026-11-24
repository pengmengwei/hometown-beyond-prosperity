/* ==========================================================================
   沉浸交互层：开场封面、场景特效绑定、鼠标微视差
   依赖 scrub-engine.js 广播的 sw:progress 事件（本地增量补丁）。
   ========================================================================== */
(function () {
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const intro = document.getElementById('intro');
  const fx = document.getElementById('fx');
  let introGone = false;

  // --- 开场封面：首次滚动/触摸后淡出 ---
  function dismissIntro() {
    if (introGone) return;
    introGone = true;
    intro.classList.add('is-gone');
  }
  window.addEventListener('scroll', () => {
    if ((window.scrollY || window.pageYOffset) > 24) dismissIntro();
  }, { passive: true });
  window.addEventListener('pointerdown', dismissIntro, { once: true, passive: true });
  // 兜底：12 秒后即使没有滚动也淡出封面
  setTimeout(dismissIntro, 12000);

  // --- 场景特效：跟随引擎进度切换 + 段落内强度包络 ---
  let curScene = 0;
  window.addEventListener('sw:progress', (e) => {
    const { near, local } = e.detail;
    const scene = near + 1;
    if (scene !== curScene) {
      curScene = scene;
      document.body.setAttribute('data-scene', String(scene));
    }
    // 段落中段最强、接缝处最弱（sin 包络），保留 0.15 底色避免闪烁
    const envelope = 0.15 + 0.85 * Math.sin(Math.PI * Math.min(1, Math.max(0, local)));
    document.documentElement.style.setProperty('--fx-intensity', envelope.toFixed(3));
  });

  // --- 键盘导航：↓/→/Space 下一章，↑/← 上一章；任意键淡出开场 ---
  const dots = () => Array.from(document.querySelectorAll('.sw-route__dot'));
  window.addEventListener('keydown', (ev) => {
    dismissIntro();
    const forward = ['ArrowDown', 'ArrowRight', 'PageDown', ' '].includes(ev.key);
    const back = ['ArrowUp', 'ArrowLeft', 'PageUp'].includes(ev.key);
    if (!forward && !back) return;
    ev.preventDefault();
    const ds = dots();
    const active = ds.findIndex((b) => b.classList.contains('is-active'));
    const idx = forward ? Math.min(ds.length - 1, active + 1) : Math.max(0, active - 1);
    if (idx >= 0 && ds[idx]) ds[idx].click();
  });

  // --- 桌面端鼠标微视差（只动特效层，不碰引擎视频） ---
  if (!reduce && window.matchMedia('(hover: hover) and (pointer: fine)').matches
      && window.innerWidth > 860) {
    let tx = 0, ty = 0, cx = 0, cy = 0;
    window.addEventListener('mousemove', (ev) => {
      tx = (ev.clientX / window.innerWidth - 0.5) * 2;
      ty = (ev.clientY / window.innerHeight - 0.5) * 2;
    }, { passive: true });
    (function loop() {
      cx += (tx - cx) * 0.05;
      cy += (ty - cy) * 0.05;
      fx.style.transform = `translate3d(${(-cx * 12).toFixed(2)}px, ${(-cy * 10).toFixed(2)}px, 0)`;
      requestAnimationFrame(loop);
    })();
  }
})();
