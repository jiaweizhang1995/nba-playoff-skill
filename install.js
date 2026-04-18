#!/usr/bin/env node
/**
 * Install the nba-playoffs skill into ~/.claude/skills/nba-playoffs/.
 * Runs automatically via npm postinstall. Cross-platform (macOS/Linux/Windows).
 */
const fs = require("fs");
const os = require("os");
const path = require("path");

const SKILL_NAME = "nba-playoffs";
const src = path.join(__dirname, "skills", SKILL_NAME);
const dst = path.join(os.homedir(), ".claude", "skills", SKILL_NAME);

function log(msg) {
  process.stdout.write(`[nba-playoff-skill] ${msg}\n`);
}

function warn(msg) {
  process.stderr.write(`[nba-playoff-skill] WARNING: ${msg}\n`);
}

function checkPython() {
  const { spawnSync } = require("child_process");
  const candidates = process.platform === "win32" ? ["python", "py", "python3"] : ["python3", "python"];
  for (const cmd of candidates) {
    const r = spawnSync(cmd, ["--version"], { stdio: "ignore" });
    if (r.status === 0) return cmd;
  }
  return null;
}

function checkRequests(py) {
  const { spawnSync } = require("child_process");
  const r = spawnSync(py, ["-c", "import requests"], { stdio: "ignore" });
  return r.status === 0;
}

try {
  if (!fs.existsSync(src)) {
    warn(`source skill dir not found: ${src}`);
    process.exit(0);
  }

  fs.mkdirSync(path.dirname(dst), { recursive: true });

  if (fs.existsSync(dst)) {
    log(`existing install at ${dst} — overwriting`);
    fs.rmSync(dst, { recursive: true, force: true });
  }

  fs.cpSync(src, dst, { recursive: true });
  log(`installed skill to ${dst}`);

  const py = checkPython();
  if (!py) {
    warn("python3 not found on PATH. Install Python 3.9+ then rerun.");
  } else if (!checkRequests(py)) {
    warn(`python '${py}' found, but 'requests' module missing. Run: ${py} -m pip install requests`);
  } else {
    log(`python OK (${py}) with 'requests' installed`);
  }

  log("done. In Claude Code, try: 'show nba playoff bracket'");
} catch (err) {
  warn(`install failed: ${err.message}`);
  process.exit(0); // non-fatal — don't break npm install
}
