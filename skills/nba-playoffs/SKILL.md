---
name: nba-playoffs
description: "Show current NBA playoff bracket as an ASCII tree (terminal) or PNG image (IM / Feishu / mobile). Includes live in-progress scores, series records, and all dates in Beijing time (UTC+8). Triggers on: 'nba playoffs', 'nba bracket', 'playoff scores', 'playoff bracket', 'nba 季后赛', '季后赛对阵', 'NBA 对阵图', '看一下季后赛', or any request about current NBA postseason matchups / scores."
allowed-tools:
  - Bash
  - Read
---

<objective>
Render the current NBA playoff bracket as text art for terminal, OR as a PNG image for IM / Feishu / mobile channels. Works for 1st Round, Conf. Semifinals, Conf. Finals, NBA Finals. All dates in Beijing time (UTC+8).
</objective>

<modes>
Two output modes. Pick based on context:

**ASCII (default, for Claude Code terminal):** print bracket to stdout, relay verbatim in fenced code block.

**PNG (for Feishu / Telegram / Discord / WeChat / any IM bridge, or when user explicitly asks for an image):** generate PNG file, return path. Do NOT print the raw ASCII in this mode — the IM bridge will upload the image.
</modes>

<execution>

### ASCII mode (default)

```bash
python3 ~/.claude/skills/nba-playoffs/scripts/render_bracket.py
```

Wrap entire stdout in fenced code block. Do not summarize, annotate, or reformat. Relay verbatim.

### PNG mode

Use PNG mode when any of:
- User asks for an image / picture / 图 / 图片.
- Session is bridged to an IM platform (Feishu / Lark / Telegram / Discord / WeChat / QQ). Hints: env var `CLAUDE_TO_IM_CHANNEL`, `CLAUDE_IM_PLATFORM`, or the claude-to-im skill is active, or user messages clearly come from an IM context.
- ASCII alignment is known to break (WeChat, mobile clients with proportional fonts).

```bash
python3 ~/.claude/skills/nba-playoffs/scripts/render_bracket.py --png /tmp/nba-bracket.png
```

Script prints the absolute PNG path to stdout on success. Then use the Read tool on that path to display the image inline (Claude Code supports image reads), or pass the path to the IM upload step.

</execution>

<error_handling>
If script exits non-zero, paste stderr. Common causes:
- `requests` Python package missing → `pip install requests`
- PNG mode: `Pillow` missing → `pip install Pillow`
- PNG mode: no monospace font found → install DejaVu Sans Mono or equivalent
- ESPN scraper schema drift → report upstream issue
</error_handling>

<output_format>
**ASCII mode:**
````
```
<script stdout verbatim>
```
````

**PNG mode:**
Read the PNG path the script printed. No preamble. No ASCII fallback in the same response.
</output_format>

<notes>
- Data: `espn.com/nba/bracket` (embedded `__espnfitt__` JSON) + `site.api.espn.com/.../scoreboard` for live scores.
- Timezone: `Asia/Shanghai` (UTC+8, CST label) on all dates.
- ASCII width: ~66 chars. Fits 80-col terminals. Breaks in proportional fonts — use PNG there.
- Current season auto-detected. No year argument.
- Cache: 5-min disk cache at `~/.cache/nba-playoffs/bracket.json`. Live scores never cached.
- CLI flags: `--png PATH` writes image file. `--font-size N` (default 18) adjusts PNG text size.
</notes>
