// Screenshot public web pages, signed out, in headless Chrome (the viewport: title and first screen).
//   CHROME=/path/to/chrome node capture-pages.mjs <out dir> <id>=<url> [<id>=<url> ...]
// Writes <out dir>/<id>.png at 1280x800, 2x scale, light colour scheme. Crop it for the beat.
// Needs: npm install puppeteer-core. CHROME is any Chrome or chrome-headless-shell binary (HyperFrames
// downloads one under ~/.cache/hyperframes/chrome/). A page that shows a relative date ("yesterday")
// ages: capture it again on the day you publish.
const [outDir, ...items] = process.argv.slice(2);
if (!process.env.CHROME || !outDir || items.length === 0) {
  console.error("usage: CHROME=/path/to/chrome node capture-pages.mjs <out dir> <id>=<url> [...]");
  process.exit(1);
}
const { default: puppeteer } = await import("puppeteer-core");  // after the usage check, so it shows without the package
const pages = items.map((s) => { const i = s.indexOf("="); return [s.slice(0, i), s.slice(i + 1)]; });
const browser = await puppeteer.launch({ executablePath: process.env.CHROME, headless: true });
const page = await browser.newPage();
await page.setViewport({ width: 1280, height: 800, deviceScaleFactor: 2 });
await page.emulateMediaFeatures([{ name: "prefers-color-scheme", value: "light" }]);
for (const [id, url] of pages) {
  await page.goto(url, { waitUntil: "networkidle2", timeout: 60000 });
  await page.screenshot({ path: `${outDir}/${id}.png` });
  console.log(id, await page.title());
}
await browser.close();
