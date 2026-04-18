#!/usr/bin/env node
/**
 * Remove ~/.claude/skills/nba-playoffs/ on npm uninstall.
 */
const fs = require("fs");
const os = require("os");
const path = require("path");

const dst = path.join(os.homedir(), ".claude", "skills", "nba-playoffs");

try {
  if (fs.existsSync(dst)) {
    fs.rmSync(dst, { recursive: true, force: true });
    process.stdout.write(`[nba-playoff-skill] removed ${dst}\n`);
  }
} catch (err) {
  process.stderr.write(`[nba-playoff-skill] uninstall WARNING: ${err.message}\n`);
}
