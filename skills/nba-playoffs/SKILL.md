---
name: nba-playoffs
description: "Show current NBA playoff bracket as an ASCII tree diagram with live in-progress scores, series records, and all dates in Beijing time (UTC+8). Triggers on: 'nba playoffs', 'nba bracket', 'playoff scores', 'playoff bracket', 'nba 季后赛', '季后赛对阵', 'NBA 对阵图', '看一下季后赛', or any request about current NBA postseason matchups / scores."
allowed-tools:
  - Bash
---

<objective>
Render the current NBA playoff bracket (all rounds) as text art, with live scores and Beijing-time dates. Works for 1st Round, Conf. Semifinals, Conf. Finals, NBA Finals.
</objective>

<execution>
Run the renderer script once. It scrapes ESPN + live scoreboard, prints bracket to stdout.

```bash
python3 "${CLAUDE_PLUGIN_ROOT:-$HOME/.claude/skills/nba-playoffs}/scripts/render_bracket.py"
```

If installed via npm, use:

```bash
python3 ~/.claude/skills/nba-playoffs/scripts/render_bracket.py
```

Wrap the entire stdout in a fenced code block so monospace alignment is preserved. Do not summarize, annotate, or reformat. Relay verbatim.

If script exits non-zero, paste stderr and tell user the ESPN scraper hit an error (likely schema drift) or the `requests` Python package is missing (`pip install requests`).
</execution>

<output_format>
````
```
<script stdout verbatim>
```
````
No preamble. No trailing commentary unless user asks.
</output_format>

<notes>
- Data: `espn.com/nba/bracket` (embedded `__espnfitt__` JSON) + `site.api.espn.com/.../scoreboard` for live scores.
- Timezone: Asia/Shanghai (UTC+8) on all dates.
- Width: ~72 chars. West half on top, East half on bottom, Finals centered below. Fits standard terminals without wrap. WeChat (proportional font): alignment still breaks.
- Current season auto-detected from ESPN. No year argument.
- Cache: 5-min disk cache at `~/.cache/nba-playoffs/bracket.json`. Live scores never cached.
- Python deps: `requests`. Install with `pip install requests` or `pip3 install requests`.
- No logos, no odds, no TV networks (by design).
</notes>
