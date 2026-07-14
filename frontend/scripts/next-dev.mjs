import { rm } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const frontendRoot = resolve(scriptDir, "..");
const devDir = resolve(frontendRoot, ".next-dev");
const nextBin = resolve(frontendRoot, "node_modules", "next", "dist", "bin", "next");

await rm(devDir, {
  force: true,
  recursive: true,
});

const suppliedArgs = process.argv.slice(2);
const hasHostname = suppliedArgs.includes("--hostname") || suppliedArgs.includes("-H");
const args = ["dev", ...(hasHostname ? [] : ["--hostname", "0.0.0.0"]), ...suppliedArgs];
const child = spawn(process.execPath, [nextBin, ...args], {
  cwd: frontendRoot,
  env: {
    ...process.env,
    NEXT_DIST_DIR: ".next-dev",
  },
  shell: false,
  stdio: "inherit",
});

child.on("exit", (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
    return;
  }

  process.exit(code ?? 0);
});
