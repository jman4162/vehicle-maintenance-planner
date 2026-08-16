import { cp, mkdir, readdir, stat } from "node:fs/promises";
import { join } from "node:path";

const root = new URL("..", import.meta.url).pathname;
const output = join(root, "public", "ocr");

async function findFile(directory, filename) {
  for (const entry of await readdir(directory)) {
    const candidate = join(directory, entry);
    if ((await stat(candidate)).isDirectory()) {
      const nested = await findFile(candidate, filename);
      if (nested) return nested;
    } else if (entry === filename) {
      return candidate;
    }
  }
  return undefined;
}

await mkdir(join(output, "core"), { recursive: true });
await mkdir(join(output, "lang"), { recursive: true });
await cp(join(root, "node_modules", "tesseract.js", "dist", "worker.min.js"), join(output, "worker.min.js"));

const coreRoot = join(root, "node_modules", "tesseract.js-core");
for (const name of await readdir(coreRoot)) {
  if (name.startsWith("tesseract-core") && (name.endsWith(".js") || name.endsWith(".wasm"))) {
    await cp(join(coreRoot, name), join(output, "core", name));
  }
}

const languageRoot = join(root, "node_modules", "@tesseract.js-data", "eng");
const language = await findFile(languageRoot, "eng.traineddata.gz");
if (!language) throw new Error("@tesseract.js-data/eng did not contain eng.traineddata.gz");
await cp(language, join(output, "lang", "eng.traineddata.gz"));
