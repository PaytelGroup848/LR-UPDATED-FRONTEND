import { spawn } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const frontendRoot = resolve(scriptDir, "..");
const nextBin = resolve(frontendRoot, "node_modules", "next", "dist", "bin", "next");

const suppliedArgs = process.argv.slice(2);
const hasHostname = suppliedArgs.includes("--hostname") || suppliedArgs.includes("-H");
const args = ["start", ...(hasHostname ? [] : ["--hostname", "0.0.0.0"]), ...suppliedArgs];

const child = spawn(process.execPath, [nextBin, ...args], {
  cwd: frontendRoot,
  env: {
    ...process.env,
    NEXT_DIST_DIR: ".next",
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
