#!/usr/bin/env node
/* QA：无头 Chrome + CDP，验证滚动页的视频可 seek、控制台无错、各滚动位置出图。
   用法：先 bash scripts/serve.sh，再 node scripts/qa.js [port] [shotdir] */
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const PORT = process.argv[2] || 8765;
const SHOTDIR = process.argv[3] || path.join(__dirname, '..', 'work', 'qa');
const VW = Number(process.env.QA_W || 1600);
const VH = Number(process.env.QA_H || 1000);
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const CDP_PORT = 9333;
fs.mkdirSync(SHOTDIR, { recursive: true });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function getWs() {
  for (let i = 0; i < 40; i++) {
    try {
      const r = await fetch(`http://127.0.0.1:${CDP_PORT}/json/list`);
      const list = await r.json();
      const page = list.find((t) => t.type === 'page' && t.webSocketDebuggerUrl);
      if (page) return page.webSocketDebuggerUrl;
    } catch {}
    await sleep(250);
  }
  throw new Error('Chrome CDP not reachable');
}

function cdp(ws) {
  let id = 0;
  const pending = new Map();
  const events = [];
  ws.addEventListener('message', (ev) => {
    const msg = JSON.parse(ev.data);
    if (msg.id && pending.has(msg.id)) { pending.get(msg.id)(msg); pending.delete(msg.id); }
    else if (msg.method) events.push(msg);
  });
  const send = (method, params = {}) => new Promise((resolve) => {
    const mid = ++id;
    pending.set(mid, resolve);
    ws.send(JSON.stringify({ id: mid, method, params }));
  });
  return { send, events };
}

(async () => {
  const chrome = spawn(CHROME, [
    '--headless=new', '--disable-gpu', '--no-sandbox',
    `--remote-debugging-port=${CDP_PORT}`,
    `--window-size=${VW},${VH}`,
    '--user-data-dir=/tmp/sw-qa-profile',
    'about:blank',
  ], { stdio: 'ignore' });

  try {
    const ws = new WebSocket(await getWs());
    await new Promise((r) => (ws.onopen = r));
    const { send, events } = cdp(ws);
    await send('Page.enable');
    await send('Runtime.enable');
    await send('Log.enable');
    if (VW <= 860) {
      await send('Emulation.setDeviceMetricsOverride', {
        width: VW, height: VH, deviceScaleFactor: 2, mobile: true,
      });
    }

    const errors = [];
    const origPush = events.push.bind(events);
    setInterval(() => {
      while (events.length) {
        const e = events.shift();
        if (e.method === 'Runtime.exceptionThrown' ||
            (e.method === 'Log.entryAdded' && ['error', 'warning'].includes(e.params.entry.level))) {
          errors.push(e.method === 'Log.entryAdded' ? e.params.entry.text : JSON.stringify(e.params.exceptionDetails));
        }
      }
    }, 300);

    await send('Page.navigate', { url: `http://127.0.0.1:${PORT}/index.html` });
    await sleep(6000);

    const evalJs = async (expr) => {
      const r = await send('Runtime.evaluate', { expression: expr, returnByValue: true });
      return r.result && r.result.result ? r.result.result.value : null;
    };

    // 1) blob seek 能力 + 视频挂载情况
    const seekInfo = await evalJs(`(() => {
      const vids = [...document.querySelectorAll('.sw-scene__video')];
      const mobileMp4 = performance.getEntriesByType('resource')
        .filter(r => r.name.includes('-m.mp4')).map(r => r.name.split('/').pop());
      return {
        totalHeight: document.querySelector('.sw-track').scrollHeight || document.body.scrollHeight,
        videos: vids.length,
        seekable: vids.filter(v => v.seekable && v.seekable.length && v.seekable.end(0) > 0).length,
        portrait: vids.filter(v => v.videoWidth > 0 && v.videoHeight > v.videoWidth).length,
        scenes: document.querySelectorAll('.sw-scene').length,
        mobileClips: [...new Set(mobileMp4)],
      };
    })()`);
    console.log('PAGE STATE:', JSON.stringify(seekInfo));

    // 2) 沿整条滚动轨迹截图（每 12% 一帧 + 首尾）
    const totalH = seekInfo.totalHeight;
    const positions = [0, .08, .2, .32, .44, .56, .68, .8, .92, .99].map((p) => Math.round(p * (totalH - 1000)));
    for (let i = 0; i < positions.length; i++) {
      await evalJs(`window.scrollTo(0, ${positions[i]})`);
      await sleep(1400);  // 等 rAF 平滑追上、视频 seek 完成
      const shot = await send('Page.captureScreenshot', { format: 'png' });
      fs.writeFileSync(path.join(SHOTDIR, `shot_${String(i).padStart(2, '0')}_p${positions[i]}.png`),
        Buffer.from(shot.result.data, 'base64'));
    }
    console.log('SHOTS ->', SHOTDIR);

    await sleep(800);
    console.log('CONSOLE ISSUES:', errors.length ? JSON.stringify(errors, null, 1) : 'none');
    ws.close();
  } finally {
    chrome.kill('SIGTERM');
  }
})().catch((e) => { console.error(e); process.exit(1); });
