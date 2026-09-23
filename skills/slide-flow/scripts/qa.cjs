// slide-flow 截图与版面检查：连到已启动的 Slidev 本地服务，逐页截图并查出界/被裁切
// 用法：node qa.cjs <config.json>   配置：{port, outDir, slides:[1,2,..]|null, chrome, width, height, shots}
// 结果：JSON 打到 stdout；进度打到 stderr
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright-chromium');

const cfg = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const base = `http://localhost:${cfg.port}`;

function checkSlide(n) {
  const frame = document.querySelector('#slide-content');
  if (!frame) return { error: 'no #slide-content', issues: [] };
  const content = document.querySelector('.slidev-page-' + n) || frame;
  const box = frame.getBoundingClientRect();
  const tol = 2;
  const out = (r) => r.right > box.right + tol || r.bottom > box.bottom + tol || r.left < box.left - tol || r.top < box.top - tol;
  const layout = content.querySelector('.slidev-layout');
  let inner = null;
  if (layout) {
    const lr = layout.getBoundingClientRect();
    const ls = getComputedStyle(layout);
    const scale = lr.width / (layout.offsetWidth || lr.width);
    inner = { left: lr.left + parseFloat(ls.paddingLeft) * scale, right: lr.right - parseFloat(ls.paddingRight) * scale,
              top: lr.top + parseFloat(ls.paddingTop) * scale, bottom: lr.bottom - parseFloat(ls.paddingBottom) * scale };
  }
  const intrude = (r) => inner && (r.right > inner.right + 6 || r.left < inner.left - 6 || r.bottom > inner.bottom + 6);
  const issues = [];
  const seen = new Set();
  const snip = (s) => (s || '').replace(/\s+/g, ' ').trim().slice(0, 40);
  const push = (kind, el, extra) => {
    const key = kind + '|' + (el && el.outerHTML ? el.outerHTML.slice(0, 80) : '') + '|' + (extra && extra.text || '');
    if (seen.has(key)) return;
    seen.add(key);
    issues.push(Object.assign({ kind, tag: el ? el.tagName.toLowerCase() : null, cls: el && el.className ? String(el.className).slice(0, 60) : '' }, extra || {}));
  };

  // 文字出界：逐个文本节点量真实的字形框
  const walker = document.createTreeWalker(content, NodeFilter.SHOW_TEXT);
  let node;
  while ((node = walker.nextNode())) {
    if (!node.textContent.trim()) continue;
    const parent = node.parentElement;
    if (!parent || getComputedStyle(parent).visibility === 'hidden') continue;
    const range = document.createRange();
    range.selectNodeContents(node);
    for (const r of range.getClientRects()) {
      if (r.width && r.height && out(r)) {
        push('text-out', parent, { text: snip(node.textContent), dx: Math.round(Math.max(r.right - box.right, box.left - r.left, 0)), dy: Math.round(Math.max(r.bottom - box.bottom, box.top - r.top, 0)) });
        break;
      }
    }
  }

  // 有底色/边框的块、图片、代码块出界
  content.querySelectorAll('*').forEach((el) => {
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') return;
    const r = el.getBoundingClientRect();
    if (!r.width || !r.height) return;
    const boxed = (cs.backgroundColor && cs.backgroundColor !== 'rgba(0, 0, 0, 0)' && cs.backgroundColor !== 'transparent') ||
      parseFloat(cs.borderTopWidth) > 0 || parseFloat(cs.borderLeftWidth) > 0 ||
      ['IMG', 'SVG', 'PRE', 'TABLE', 'CANVAS', 'VIDEO', 'IFRAME'].includes(el.tagName.toUpperCase());
    if (boxed && out(r) && el !== content) {
      push('box-out', el, { dx: Math.round(Math.max(r.right - box.right, box.left - r.left, 0)), dy: Math.round(Math.max(r.bottom - box.bottom, box.top - r.top, 0)) });
    } else if (boxed && intrude(r) && el !== layout && !el.closest('.sf-cover-mark') && !el.classList.contains('sf-pageno') && !el.classList.contains('sf-cover-mark')) {
      push('margin', el, { dx: Math.round(Math.max(r.right - inner.right, inner.left - r.left, 0)), dy: Math.round(Math.max(r.bottom - inner.bottom, 0)) });
    }
    // 内容被裁切：溢出被隐藏或出现滚动
    const clipX = el.scrollWidth > el.clientWidth + 2 && ['hidden', 'auto', 'scroll', 'clip'].includes(cs.overflowX);
    const clipY = el.scrollHeight > el.clientHeight + 2 && ['hidden', 'auto', 'scroll', 'clip'].includes(cs.overflowY);
    const ellipsis = cs.textOverflow === 'ellipsis' && el.scrollWidth > el.clientWidth + 1;
    if ((clipX || clipY || ellipsis) && el.clientWidth > 0 && !el.classList.contains('slidev-layout')) {
      push('clipped', el, { text: snip(el.textContent), x: clipX || ellipsis, y: clipY });
    }
  });

  // 图片没加载出来
  content.querySelectorAll('img').forEach((img) => {
    if (!img.complete || img.naturalWidth === 0) push('img-broken', img, { src: img.getAttribute('src') });
  });

  const title = content.querySelector('h1, h2');
  return { title: title ? snip(title.textContent) : '', issues };
}

(async () => {
  const browser = await chromium.launch({ executablePath: cfg.chrome });
  const page = await browser.newPage({ viewport: { width: cfg.width || 1280, height: cfg.height || 720 }, deviceScaleFactor: 1 });
  await page.goto(`${base}/1?print`, { waitUntil: 'networkidle', timeout: 60000 });
  const total = await page.evaluate(() => (window.__slidev__ && window.__slidev__.nav && window.__slidev__.nav.total) || 0);
  const list = (cfg.slides && cfg.slides.length ? cfg.slides : Array.from({ length: total }, (_, i) => i + 1)).filter((n) => n >= 1 && n <= total);
  if (cfg.shots) fs.mkdirSync(cfg.outDir, { recursive: true });
  const pad = String(total).length < 2 ? 2 : String(total).length;
  const slides = [];
  for (const n of list) {
    await page.goto(`${base}/${n}?print`, { waitUntil: 'networkidle', timeout: 60000 });
    await page.evaluate(() => document.fonts && document.fonts.ready);
    await page.waitForTimeout(cfg.settleMs || 400);
    const res = await page.evaluate(checkSlide, n);
    let shot = null;
    if (cfg.shots) {
      shot = path.join(cfg.outDir, `slide-${String(n).padStart(pad, '0')}.png`);
      const clip = await page.evaluate((k) => {
        const el = document.querySelector('.slidev-page-' + k) || document.querySelector('#slide-content');
        const r = el.getBoundingClientRect();
        const x = Math.ceil(r.left), y = Math.ceil(r.top);
        return { x, y, width: Math.floor(r.right) - x, height: Math.floor(r.bottom) - y };
      }, n);
      await page.screenshot({ path: shot, clip });
    }
    slides.push(Object.assign({ n, shot }, res));
    process.stderr.write(`qa: slide ${n}/${total} ${res.issues ? res.issues.length : 0} issue(s)\n`);
  }
  await browser.close();
  process.stdout.write(JSON.stringify({ total, slides }));
})().catch((e) => {
  process.stderr.write(String(e && e.stack || e) + '\n');
  process.exit(1);
});
