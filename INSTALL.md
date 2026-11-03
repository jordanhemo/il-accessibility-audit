# התקנה / Installation

הסקיל כתוב בפורמט [Agent Skills](https://agentskills.io) (תיקייה עם `SKILL.md`), שנתמך על ידי Claude, Codex CLI וכלים נוספים. סוכן שלא תומך בפורמט יכול להריץ את הסורק ישירות.

The skill uses the [Agent Skills](https://agentskills.io) format (a folder with a `SKILL.md`), supported by Claude, Codex CLI and others. Any other agent can run the scanner directly.

**Download:** https://github.com/jordanhemo/il-accessibility-audit/raw/main/dist/il-accessibility-audit.zip
(same content as `.skill`: https://github.com/jordanhemo/il-accessibility-audit/raw/main/dist/il-accessibility-audit.skill)

Requires Python 3. No packages to install.

---

## Claude Code

**As a plugin (recommended).** This repository is a plugin marketplace. At the Claude Code prompt:

```
/plugin install il-accessibility-audit --marketplace jordanhemo/il-accessibility-audit
```

Answer `y` to add the marketplace, then pick a scope. From a shell:
`claude plugin install il-accessibility-audit --marketplace jordanhemo/il-accessibility-audit`.
In the desktop app: + next to the prompt box → Plugins → Add marketplace `jordanhemo/il-accessibility-audit` → Add plugin.
Get later versions with `/plugin marketplace update il-accessibility-audit`.

**As a plain skill folder:**

```bash
git clone https://github.com/jordanhemo/il-accessibility-audit.git
cp -r il-accessibility-audit/il-accessibility-audit ~/.claude/skills/
```

Or for a single project: copy the folder to `<project>/.claude/skills/`.

## Claude.ai / Claude desktop app

1. Download the `.skill` file (link above).
2. In Settings, open the Skills section and upload the file.
3. Ask Claude to audit a project's accessibility.

## Codex CLI (OpenAI)

```bash
git clone https://github.com/jordanhemo/il-accessibility-audit.git
mkdir -p ~/.codex/skills
cp -r il-accessibility-audit/il-accessibility-audit ~/.codex/skills/
```

Restart Codex. Older Codex versions gate skills behind a flag: run `codex --enable skills`.
For a single project, Codex also discovers skills under `<project>/.agents/skills/`.

## Cursor, Gemini CLI, Aider and other agents

Copy the `il-accessibility-audit/` folder into your project (or anywhere), then point the agent at
it, for example:

> Read `il-accessibility-audit/SKILL.md` and follow it to audit this project.

If the agent can run shell commands, it can also run the scanner directly:

```bash
python3 il-accessibility-audit/scripts/scan.py . --format md --fix --report accessibility-report.md
```

## Without any agent

The scanner is a normal command-line tool:

```bash
python3 il-accessibility-audit/scripts/scan.py <project_dir>                  # JSON findings
python3 il-accessibility-audit/scripts/scan.py <project_dir> --format md       # Hebrew markdown report
python3 il-accessibility-audit/scripts/scan.py <project_dir> --format md --fix # also apply the safe fixes
```

---

## שימוש / Usage

כותבים לסוכן בשפה חופשית, למשל:

> תבדוק אם האתר בתיקייה הזו עומד בתקן הנגישות הישראלי ותתקן מה שאפשר

Or in English:

> Audit this project for Israeli accessibility law (IS 5568) and fix what is safe to fix.
