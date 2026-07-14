import { rm } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const frontendRoot = resolve(scriptDir, "..");
const targets = [".next", ".next-dev"];

for (const target of targets) {
  await rm(resolve(frontendRoot, target), {
    force: true,
    recursive: true,
  });
}
