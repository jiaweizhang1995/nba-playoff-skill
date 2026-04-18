# nba-playoff-skill

A [Claude Code](https://claude.com/claude-code) skill that renders the current NBA playoff bracket as an ASCII tree, with live in-progress scores, series records, and all dates in Beijing time (UTC+8). Data source: ESPN.

```
NBA PLAYOFFS 2025-26 -- 1st Round
Updated 2026-04-19 02:09 CST  (source: ESPN)

─────────────────────────────── WESTERN ────────────────────────────────
╭────────────────────╮
│1 Thunder           │
│8 Suns              │─┐
│04-20 03:30 CST     │ │ ╭────────────────────╮
╰────────────────────╯ │ │TBD                 │
                       ├─│TBD                 │─┐
...
```

## Requirements

- **Claude Code** installed ([download](https://claude.com/claude-code))
- **Python 3.9+** on PATH
- Python package `requests` (`pip install requests`)
- **Node.js 16+** (only for npm install method)

## Install

### Option A — Plugin marketplace (recommended)

Inside Claude Code, run:

```
/plugin marketplace add jiaweizhang1995/nba-playoff-skill
/plugin install nba-playoff-skill@jimmyzhang-skills
```

### Option B — npm (global)

```bash
npm install -g nba-playoff-skill
```

Postinstall copies the skill into `~/.claude/skills/nba-playoffs/`.

### Option C — manual

```bash
git clone https://github.com/jiaweizhang1995/nba-playoff-skill.git
cp -r nba-playoff-skill/skills/nba-playoffs ~/.claude/skills/
```

## Usage

In any Claude Code session, ask any of:

- `show nba playoff bracket`
- `nba playoffs`
- `看一下季后赛`
- `NBA 对阵图`

Claude auto-invokes the skill and prints the bracket.

## Uninstall

**npm:**

```bash
npm uninstall -g nba-playoff-skill
```

**Plugin:**

```
/plugin uninstall nba-playoff-skill
```

**Manual:** `rm -rf ~/.claude/skills/nba-playoffs`

## How it works

The skill is a single `SKILL.md` + one Python script. On invocation, Claude runs:

```bash
python3 ~/.claude/skills/nba-playoffs/scripts/render_bracket.py
```

The script scrapes `espn.com/nba/bracket` (embedded JSON blob) and fuses it with `site.api.espn.com`'s live scoreboard. Bracket schedule is disk-cached for 5 minutes; live scores are always fresh.

## Notes

- All dates are rendered in `Asia/Shanghai` (UTC+8, CST).
- Works for 1st Round → Conf. Semifinals → Conf. Finals → NBA Finals. Off-season shows empty TBD cells.
- ASCII output is ~72 chars wide. Looks correct in monospace terminals. Breaks in WeChat / proportional fonts.
- No logos, no odds, no TV networks — by design.

## License

MIT © jimmyzhang95
