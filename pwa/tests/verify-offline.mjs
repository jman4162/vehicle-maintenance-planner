import assert from "node:assert/strict";
import { readdir, readFile, stat } from "node:fs/promises";
import { join } from "node:path";

const root = join(process.cwd(), "dist");

async function files(directory) {
  const output = [];
  for (const entry of await readdir(directory)) {
    const candidate = join(directory, entry);
    if ((await stat(candidate)).isDirectory()) output.push(...await files(candidate));
    else output.push(candidate);
  }
  return output;
}

const built = await files(root);
assert.ok(built.some((path) => path.endsWith("sw.js")), "Workbox service worker is missing");
assert.ok(built.some((path) => path.endsWith("eng.traineddata.gz")), "offline OCR language data is missing");
assert.ok(built.some((path) => path.endsWith("worker.min.js")), "offline OCR worker is missing");

const scripts = built.filter((path) => path.endsWith(".js"));
let applicationCode = "";
for (const script of scripts) {
  const text = await readFile(script, "utf8");
  applicationCode += text;
  assert.doesNotMatch(text, /fonts\.googleapis\.com|google-analytics|segment\.com|plausible\.io/i);
}
assert.match(applicationCode, /\/ocr\/worker\.min\.js/);
assert.match(applicationCode, /\/ocr\/core/);
assert.match(applicationCode, /\/ocr\/lang/);
const serviceWorker = await readFile(built.find((path) => path.endsWith("sw.js")), "utf8");
assert.match(serviceWorker, /eng\.traineddata\.gz/);
assert.match(serviceWorker, /worker\.min\.js/);

console.log(`Offline build verified: ${built.length} files, local OCR and service worker present.`);
