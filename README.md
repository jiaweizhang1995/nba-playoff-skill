# nba-playoff-skill

**[English](#english)** · **[中文](#中文)**

---

<a name="english"></a>

## English

A [Claude Code](https://claude.com/claude-code) skill that draws the current NBA playoff bracket as an ASCII tree — live scores, series records, all dates in Beijing time (UTC+8).

### Preview

```
NBA PLAYOFFS 2025-26 -- 1st Round
─────────────────────────── WESTERN ────────────────────────────
╭────────────────────╮
│1 Thunder           │
│8 Suns              │─┐
│04-20 03:30 CST     │ │ ╭────────────────────╮
╰────────────────────╯ │ │TBD                 │
                       ├─│TBD                 │─┐
...
```

### Requirements

- Claude Code
- Python 3.9+ with `requests` → `pip install requests`
- Node.js 16+ (npm install method only)

### Install

**Option A — npm (recommended):**

```bash
npm install -g nba-playoff-skill
```

**Option B — Claude Code plugin marketplace:**

```
/plugin marketplace add jiaweizhang1995/nba-playoff-skill
/plugin install nba-playoff-skill@jimmyzhang-skills
```

### Usage

In any Claude Code session, say any of:

- `show nba playoff bracket`
- `nba playoffs`
- `看一下季后赛`

Claude auto-runs the skill and prints the bracket.

### Uninstall

```bash
npm uninstall -g nba-playoff-skill
```

### License

MIT © [jimmyzhang95](https://github.com/jiaweizhang1995)

---

<a name="中文"></a>

## 中文

一个 [Claude Code](https://claude.com/claude-code) skill — 用 ASCII 树状图显示当前 NBA 季后赛对阵。实时比分、系列赛战况、所有日期都是北京时间 (UTC+8)。

### 预览

```
NBA PLAYOFFS 2025-26 -- 1st Round
─────────────────────────── WESTERN ────────────────────────────
╭────────────────────╮
│1 Thunder           │
│8 Suns              │─┐
│04-20 03:30 CST     │ │ ╭────────────────────╮
╰────────────────────╯ │ │TBD                 │
                       ├─│TBD                 │─┐
...
```

### 依赖

- Claude Code
- Python 3.9+，带 `requests` 包 → `pip install requests`
- Node.js 16+（仅 npm 安装方式需要）

### 安装

**方式 A — npm（推荐）：**

```bash
npm install -g nba-playoff-skill
```

**方式 B — Claude Code 插件市场：**

```
/plugin marketplace add jiaweizhang1995/nba-playoff-skill
/plugin install nba-playoff-skill@jimmyzhang-skills
```

### 使用

在任意 Claude Code 会话里，说以下任意一句：

- `看一下季后赛`
- `NBA 对阵图`
- `show nba playoff bracket`

Claude 自动调用 skill，打印对阵图。

### 卸载

```bash
npm uninstall -g nba-playoff-skill
```

### 许可证

MIT © [jimmyzhang95](https://github.com/jiaweizhang1995)
