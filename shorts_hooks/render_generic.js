// node render_generic.js WORKDIR OUT_FRAMES_DIR [frames=46] [sub=8]  — serves shorts_hooks/ over http, renders motion-blurred frames
const { chromium } = require('/opt/node-tools/node_modules/playwright');
const fs = require('fs'), path = require('path'), http = require('http');
const ROOT = __dirname;
const srv = http.createServer((q, r) => {
  const f = path.join(ROOT, decodeURIComponent(q.url.split('?')[0]));
  fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); r.end(); return; }
    r.writeHead(200, { 'Content-Type': f.endsWith('.html') ? 'text/html' : f.endsWith('.json') ? 'application/json' : 'image/png' }); r.end(d); });
});
(async () => {
  const [work, out, nf = 46, sub = 8] = process.argv.slice(2); fs.mkdirSync(out, { recursive: true });
  await new Promise(r => srv.listen(0, r)); const port = srv.address().port;
  const browser = await chromium.launch({ args: ['--force-color-profile=srgb'] });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  page.on('pageerror', e => console.log('ERR', e.message)); page.on('console', m => console.log('page:', m.text()));
  await page.goto(`http://127.0.0.1:${port}/hook_generic.html?dir=${encodeURIComponent(path.relative(ROOT, path.resolve(work)))}`);
  await page.evaluate(() => window.__ready);
  if (process.env.STILLS) {
    for (const t of process.env.STILLS.split(',').map(Number)) {
      const url = await page.evaluate(t => { renderAt(t); return document.getElementById('c').toDataURL('image/png'); }, t);
      fs.writeFileSync(`${out}/still_${t.toFixed(3)}.png`, Buffer.from(url.split(',')[1], 'base64'));
    }
  } else for (let f = 0; f < +nf; f++) {
    const url = await page.evaluate(([f, s]) => renderFrame(f, 30, s), [f, +sub]);
    fs.writeFileSync(`${out}/h${String(f).padStart(3, '0')}.png`, Buffer.from(url.split(',')[1], 'base64'));
  }
  await browser.close(); srv.close();
})();
