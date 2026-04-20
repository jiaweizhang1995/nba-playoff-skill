#!/usr/bin/env python3
"""
NBA Playoffs bracket renderer — stacked layout (West above East, Finals below).

Scrapes ESPN bracket + live scoreboard, prints ASCII tree bracket with all
dates in Asia/Shanghai (UTC+8).

Speed optimizations:
- 5-minute disk cache of bracket JSON (schedule changes rarely; scores always fresh)
- Parallel fetch of bracket + scoreboard on cache miss
- Graceful stale-cache fallback if upstream fails
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

BRACKET_URL = "https://www.espn.com/nba/bracket"
SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15"
BJT = ZoneInfo("Asia/Shanghai")

CACHE_DIR = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "nba-playoffs"
CACHE_FILE = CACHE_DIR / "bracket.json"
CACHE_TTL = 300  # seconds

BOX_W = 20
BLOCK_H = 5
GAP = 2


def _http_get(url: str, timeout: float) -> requests.Response:
    r = requests.get(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip"}, timeout=timeout)
    r.raise_for_status()
    return r


def fetch_bracket_live() -> dict:
    html = _http_get(BRACKET_URL, 15).text
    idx = html.find("window['__espnfitt__']")
    if idx < 0:
        raise RuntimeError("ESPN bracket page changed: __espnfitt__ not found")
    start = html.find("{", idx)
    depth = 0
    end = -1
    for i in range(start, len(html)):
        c = html[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    if end < 0:
        raise RuntimeError("ESPN bracket page changed: unmatched braces")
    return json.loads(html[start:end])["page"]["content"]["bracket"]


def load_bracket() -> dict:
    """Cache-aware bracket loader. Returns fresh or stale cache on upstream failure."""
    now = time.time()
    if CACHE_FILE.exists() and now - CACHE_FILE.stat().st_mtime < CACHE_TTL:
        try:
            return json.loads(CACHE_FILE.read_text())
        except Exception:
            pass
    try:
        b = fetch_bracket_live()
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps(b))
        return b
    except Exception:
        if CACHE_FILE.exists():
            return json.loads(CACHE_FILE.read_text())
        raise


def fetch_scoreboard() -> dict:
    try:
        return _http_get(SCOREBOARD_URL, 10).json()
    except Exception:
        return {"events": []}


def load_all() -> tuple[dict, dict]:
    """Parallel-load bracket (cached or live) + scoreboard."""
    now = time.time()
    cache_fresh = CACHE_FILE.exists() and now - CACHE_FILE.stat().st_mtime < CACHE_TTL
    if cache_fresh:
        try:
            bracket = json.loads(CACHE_FILE.read_text())
            live = fetch_scoreboard()
            return bracket, live
        except Exception:
            pass
    with ThreadPoolExecutor(max_workers=2) as ex:
        f_b = ex.submit(load_bracket)
        f_s = ex.submit(fetch_scoreboard)
        bracket = f_b.result()
        live = f_s.result()
    return bracket, live


def bjt(iso: str) -> str:
    if not iso:
        return ""
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(BJT).strftime("%m-%d %H:%M")


def compact_status(detail: str) -> str:
    """ESPN 'shortDetail' → compact form. '3:51 - 2nd' → 'Q2 3:51'."""
    if not detail:
        return ""
    m = re.match(r"^(\S+)\s*-\s*(\d+)(?:st|nd|rd|th)\s*$", detail.strip())
    if m:
        t, q = m.group(1), m.group(2)
        if t.lower() == "end":
            return f"End Q{q}"
        return f"Q{q} {t}"
    d = detail.strip()
    d = d.replace("Halftime", "Half")
    return d


def compute_series(series_scores: dict, live_events: dict):
    """Return (wins_A, wins_B, live_status, live_score) for one series.

    Wins come *directly* from the bracket JSON's per-game
    ``statusState`` / ``winnerA`` / ``scoreA`` / ``scoreB`` fields. We do not
    cross-reference today's live scoreboard for completed games because ESPN's
    scoreboard drops games older than ~24h, which would silently zero-out any
    series whose last game wasn't played today (e.g. Lakers 1-0 Rockets
    rendering as 0-0 the day after Game 1).

    The live scoreboard is still consulted, but *only* to enrich an in-progress
    game with quarter/clock detail ("Q3 4:21") that the bracket JSON lacks.
    """
    if not series_scores:
        return 0, 0, None, None

    live_by_id = {str(ev.get("id")): ev for ev in live_events.get("events", [])}
    w1 = w2 = 0
    live_status = None
    live_score = None

    c1_name = series_scores["competitors"][0].get("name", "")
    c2_name = series_scores["competitors"][1].get("name", "")

    for comp in series_scores.get("competitions", []):
        state = comp.get("statusState")
        winner_a = comp.get("winnerA")
        score_a = comp.get("scoreA")
        score_b = comp.get("scoreB")

        if state == "post":
            # Primary signal: winnerA flag (True → A won, False → B won).
            if winner_a is True:
                w1 += 1
            elif winner_a is False:
                w2 += 1
            # Fallback: ESPN sometimes leaves winnerA as None even after a
            # final — fall back to the score comparison we already have.
            elif score_a is not None and score_b is not None:
                if score_a > score_b:
                    w1 += 1
                elif score_b > score_a:
                    w2 += 1
            # else: no reliable signal, skip

        elif state == "in":
            # In-progress game: bracket JSON carries live scoreA/scoreB too,
            # so we can show a score even if scoreboard enrichment fails.
            if score_a is not None and score_b is not None:
                live_score = f"{score_a}-{score_b}"

            ev = live_by_id.get(str(comp.get("id")))
            if ev:
                live_status = compact_status(
                    ev.get("status", {}).get("type", {}).get("shortDetail", "")
                )
                # Scoreboard score is more up-to-the-minute than bracket JSON;
                # overwrite if both teams are present.
                teams = ev.get("competitions", [{}])[0].get("competitors", [])
                by = {t.get("team", {}).get("name", ""): t.get("score") for t in teams}
                if by.get(c1_name) is not None and by.get(c2_name) is not None:
                    live_score = f"{by.get(c1_name)}-{by.get(c2_name)}"
            elif comp.get("statusDetail"):
                # No live scoreboard match — fall back to bracket's own label.
                live_status = compact_status(comp.get("statusDetail", ""))

    return w1, w2, live_status, live_score


def matchup_box(m: dict, live: dict) -> list[str]:
    c1 = m.get("competitorOne", {})
    c2 = m.get("competitorTwo", {})

    def label(c):
        seed = c.get("seed")
        name = c.get("name", "TBD")
        return f"{seed} {name}" if seed else name

    series = m.get("seriesScores") or {}
    w1, w2, live_status, live_score = compute_series(series, live)
    inner = BOX_W - 2

    def line(c, w):
        tag = label(c)
        if m.get("isSeries") and (w1 + w2 > 0):
            num = f" {w}"
            tag = (tag[: inner - len(num)].ljust(inner - len(num))) + num
        else:
            tag = tag[:inner].ljust(inner)
        return tag

    l1 = line(c1, w1)
    l2 = line(c2, w2)

    if live_status and live_score:
        status = f"* {live_score} {live_status}"
    elif m.get("isSeriesComplete"):
        winner = c1 if c1.get("seriesWinner") else c2 if c2.get("seriesWinner") else None
        abbr = (winner or {}).get("abbreviation", "???")
        status = f"{abbr} wins {max(w1, w2)}-{min(w1, w2)}"
    elif m.get("isSeries") and (w1 > 0 or w2 > 0):
        leader = c1 if w1 >= w2 else c2
        status = f"{leader.get('abbreviation','???')} {max(w1, w2)}-{min(w1, w2)}"
    else:
        d = m.get("date")
        status = f"{bjt(d)} CST" if d else "TBD"

    status = status[:inner].ljust(inner)
    top = "╭" + "─" * inner + "╮"
    bot = "╰" + "─" * inner + "╯"
    return [top, f"│{l1}│", f"│{l2}│", f"│{status}│", bot]


def empty_box(label: str = "TBD") -> list[str]:
    inner = BOX_W - 2
    return [
        "╭" + "─" * inner + "╮",
        "│" + "TBD".ljust(inner) + "│",
        "│" + "TBD".ljust(inner) + "│",
        "│" + "TBD".ljust(inner) + "│",
        "╰" + "─" * inner + "╯",
    ]


def blank(w: int) -> str:
    return " " * w


def build_r1_column(by_round: dict, locs: tuple[int, ...], live: dict) -> list[str]:
    rows = []
    for loc in locs:
        m = by_round.get(1, {}).get(loc)
        rows.extend(matchup_box(m, live) if m and m.get("competitorOne", {}).get("name") != "TBD" else empty_box())
        rows.extend([blank(BOX_W)] * GAP)
    return rows[:-GAP]


def build_rN_column(by_round: dict, round_id: int, locs: tuple[int, ...], live: dict, total_rows: int) -> list[str]:
    col = [blank(BOX_W) for _ in range(total_rows)]
    if round_id == 2:
        for pair_idx, loc in enumerate(locs):
            pair_top = pair_idx * (BLOCK_H * 2 + GAP * 2)
            pair_bot = pair_top + (BLOCK_H * 2 + GAP) - 1
            center = (pair_top + pair_bot) // 2
            m = by_round.get(2, {}).get(loc)
            box = matchup_box(m, live) if m and m.get("competitorOne", {}).get("name") != "TBD" else empty_box()
            start = center - len(box) // 2
            for i, ln in enumerate(box):
                col[start + i] = ln
    elif round_id == 3:
        loc = locs[0]
        center = total_rows // 2
        m = by_round.get(3, {}).get(loc)
        box = matchup_box(m, live) if m and m.get("competitorOne", {}).get("name") != "TBD" else empty_box()
        start = center - len(box) // 2
        for i, ln in enumerate(box):
            col[start + i] = ln
    return col


def connector(total_rows: int, kind: str) -> list[str]:
    """kind: 'r1r2' (4 R1 pairs → 2 R2) or 'r2r3' (2 R2 → 1 R3)."""
    W = 3
    col = [blank(W) for _ in range(total_rows)]
    if kind == "r1r2":
        for pair_idx in range(2):
            top = pair_idx * (BLOCK_H * 2 + GAP * 2) + BLOCK_H // 2
            bot = pair_idx * (BLOCK_H * 2 + GAP * 2) + BLOCK_H + GAP + BLOCK_H // 2
            mid = (top + bot) // 2
            for r in range(top, bot + 1):
                if r == top:
                    col[r] = "─┐ "
                elif r == bot:
                    col[r] = "─┘ "
                elif r == mid:
                    col[r] = " ├─"
                else:
                    col[r] = " │ "
    elif kind == "r2r3":
        c_top = (BLOCK_H * 2 + GAP - 1) // 2
        c_bot = (BLOCK_H * 2 + GAP * 2) + (BLOCK_H * 2 + GAP - 1) // 2
        mid = total_rows // 2
        for r in range(c_top, c_bot + 1):
            if r == c_top:
                col[r] = "─┐ "
            elif r == c_bot:
                col[r] = "─┘ "
            elif r == mid:
                col[r] = " ├─"
            else:
                col[r] = " │ "
    return col


def join_cols(cols: list[list[str]]) -> str:
    h = len(cols[0])
    return "\n".join("".join(row) for row in zip(*cols))


def render_conference(by_round: dict, conf: str, live: dict) -> str:
    if conf == "west":
        r1_locs = (1, 2, 3, 4)
        r2_locs = (1, 2)
        r3_locs = (1,)
        label = "WESTERN"
    else:
        r1_locs = (5, 6, 7, 8)
        r2_locs = (3, 4)
        r3_locs = (2,)
        label = "EASTERN"

    r1 = build_r1_column(by_round, r1_locs, live)
    total_rows = len(r1)
    r2 = build_rN_column(by_round, 2, r2_locs, live, total_rows)
    r3 = build_rN_column(by_round, 3, r3_locs, live, total_rows)

    cols = [
        r1,
        connector(total_rows, "r1r2"),
        r2,
        connector(total_rows, "r2r3"),
        r3,
    ]
    body = join_cols(cols)
    total_width = BOX_W * 3 + 3 * 2
    banner = f" {label} ".center(total_width, "─")
    return banner + "\n" + body


def render_finals(by_round: dict, live: dict) -> str:
    total_width = BOX_W * 3 + 3 * 2
    m = by_round.get(4, {}).get(1)
    box = matchup_box(m, live) if m and m.get("competitorOne", {}).get("name") != "TBD" else empty_box()
    pad = (total_width - BOX_W) // 2
    banner = " NBA FINALS ".center(total_width, "─")
    lines = [banner] + [" " * pad + ln for ln in box]
    return "\n".join(lines)


def render(bracket: dict, live: dict) -> str:
    by_round = {1: {}, 2: {}, 3: {}, 4: {}}
    for m in bracket.get("matchups", []):
        r = m.get("roundId")
        if r in by_round:
            by_round[r][m.get("bracketLocation")] = m

    now_cst = datetime.now(BJT).strftime("%Y-%m-%d %H:%M")
    round_label = {
        1: "1st Round",
        2: "Conf. Semifinals",
        3: "Conf. Finals",
        4: "NBA Finals",
    }.get(bracket.get("activeRound", 1), "Playoffs")

    header = (
        f"NBA PLAYOFFS {bracket.get('season','')}  --  {round_label}\n"
        f"Updated {now_cst} CST  (source: ESPN)\n"
    )
    return (
        header
        + "\n"
        + render_conference(by_round, "west", live)
        + "\n\n"
        + render_conference(by_round, "east", live)
        + "\n\n"
        + render_finals(by_round, live)
        + "\n"
    )


FONT_CANDIDATES = [
    "/System/Library/Fonts/Menlo.ttc",
    "/System/Library/Fonts/SFNSMono.ttf",
    "/Library/Fonts/SF-Mono-Regular.otf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/TTF/DejaVuSansMono.ttf",
    "C:/Windows/Fonts/consola.ttf",
    "C:/Windows/Fonts/cour.ttf",
]


def _find_mono_font(size: int):
    from PIL import ImageFont

    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    raise RuntimeError(
        "No monospace TTF font found. Install one (e.g. DejaVu Sans Mono) or "
        "edit FONT_CANDIDATES in render_bracket.py."
    )


def render_png(text: str, out_path: Path, font_size: int = 18) -> None:
    try:
        from PIL import Image, ImageDraw
    except ImportError as e:
        raise RuntimeError(
            "PNG output requires Pillow. Install with: pip install Pillow"
        ) from e

    font = _find_mono_font(font_size)
    lines = text.rstrip("\n").split("\n")

    bbox = font.getbbox("M")
    char_w = bbox[2] - bbox[0]
    line_h = int((bbox[3] - bbox[1]) * 1.4) + 2

    max_cols = max((len(ln) for ln in lines), default=1)
    pad = 24
    img_w = char_w * max_cols + pad * 2
    img_h = line_h * len(lines) + pad * 2

    bg = (22, 22, 24)
    fg = (230, 230, 230)
    img = Image.new("RGB", (img_w, img_h), bg)
    draw = ImageDraw.Draw(img)
    for i, line in enumerate(lines):
        draw.text((pad, pad + i * line_h), line, font=font, fill=fg)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(out_path), "PNG")


def main() -> int:
    parser = argparse.ArgumentParser(description="Render NBA playoff bracket.")
    parser.add_argument(
        "--png",
        metavar="PATH",
        help="Render bracket as PNG to PATH instead of ASCII to stdout.",
    )
    parser.add_argument(
        "--font-size",
        type=int,
        default=18,
        help="PNG font size (default: 18).",
    )
    args = parser.parse_args()

    try:
        bracket, live = load_all()
    except Exception as e:
        print(f"ERROR fetching bracket: {e}", file=sys.stderr)
        return 1

    text = render(bracket, live)

    if args.png:
        try:
            out = Path(args.png).expanduser().resolve()
            render_png(text, out, font_size=args.font_size)
            print(str(out))
            return 0
        except Exception as e:
            print(f"ERROR rendering PNG: {e}", file=sys.stderr)
            return 2

    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
