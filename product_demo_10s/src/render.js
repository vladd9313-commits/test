// usage: node render.js OUTDIR [t0 t1] [stills: comma list]  — renders 4 subframes per 60fps frame (180° shutter)
const { chromium } = require('/opt/node-tools/node_modules/playwright');
const fs = require('fs'), path = require('path');
(async () => {
  const out = process.argv[2]; fs.mkdirSync(out, { recursive: true });
  const browser = await chromium.launch({ args: ['--disable-gpu-vsync', '--force-color-profile=srgb'] });
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  page.on('console', m => console.log('page:', m.text())); page.on('pageerror', e => console.log('ERR', e.message));
  await page.goto('file://' + path.resolve(__dirname, 'demo.html'));
  await page.evaluate(() => window.__ready);
  const stage = await page.$('#stage');
  if (process.argv[3] === 'stills') {
    for (const t of process.argv[4].split(',').map(Number)) {
      await page.evaluate(t => renderAt(t), t);
      await stage.screenshot({ path: `${out}/still_${t.toFixed(2)}.png` });
    }
  } else {
    const fps = 60, SUB = 4, sh = 0.5 / fps;     // exposure = half a frame
    const f0 = Math.round((+process.argv[3] || 0) * fps), f1 = Math.round((+process.argv[4] || 10) * fps);
    const T = Date.now();
    for (let f = f0; f < f1; f++) for (let k = 0; k < SUB; k++) {
      const t = Math.max(0, f / fps - sh + sh * (k + 1) / SUB);
      await page.evaluate(t => renderAt(t), t);
      await stage.screenshot({ path: `${out}/s${String((f - f0) * SUB + k).padStart(5, '0')}.png` });
      if (k == 0 && f % 60 == 0) console.log('frame', f, ((Date.now() - T) / 1000).toFixed(0) + 's');
    }
  }
  await browser.close();
})();
