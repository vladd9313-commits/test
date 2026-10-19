// node render_hook.js HOOK.html OUTDIR (frames FPS DUR SUB | stills t1,t2,...)
// frames: SUB subframes per frame over a 180° shutter, numbered s00000.png...; average them with ffmpeg tmix.
const { chromium } = require('/opt/node-tools/node_modules/playwright');
const fs = require('fs'), path = require('path');
(async () => {
  const [html, out, mode, a, b, c] = process.argv.slice(2); fs.mkdirSync(out, { recursive: true });
  const browser = await chromium.launch({ args: ['--allow-file-access-from-files', '--force-color-profile=srgb'] });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  page.on('pageerror', e => console.log('ERR', e.message));
  await page.goto('file://' + path.resolve(html)); await page.evaluate(() => window.__ready);
  const el = await page.$('canvas');
  if (mode === 'stills') {
    for (const t of a.split(',').map(Number)) { await page.evaluate(t => renderAt(t), t); await el.screenshot({ path: `${out}/still_${t.toFixed(3)}.png` }); }
  } else {
    const fps = +a, n = Math.round(+b * fps), sub = +c, sh = 0.5 / fps;
    for (let f = 0; f < n; f++) for (let k = 0; k < sub; k++) {
      const t = Math.max(0, f / fps - sh / 2 + sh * (k + .5) / sub);
      await page.evaluate(t => renderAt(t), t);
      await el.screenshot({ path: `${out}/s${String(f * sub + k).padStart(5, '0')}.png` });
    }
  }
  await browser.close();
})();
