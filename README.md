# בודק נגישות ישראלי · IL Accessibility Audit

סקיל לסוכני AI (Claude, Codex CLI ואחרים) שסורק פרויקט אינטרנט לפי **תקן ישראלי 5568** ו**תקנות נגישות השירות (תשע"ג-2013)**, מפיק דוח בעברית ומתקן אוטומטית את מה שבטוח לתקן.

An agent skill that audits a web project against **Israeli Standard 5568** (WCAG 2.0/2.1 AA plus Israel-specific rules), writes a Hebrew report and auto-fixes the unambiguous findings.

- **אתר והסבר:** https://github.com/jordanhemo/il-accessibility-site
- **התקנה / Install:** [INSTALL.md](INSTALL.md)
- **הורדה / Download:** [dist/il-accessibility-audit.skill](dist/il-accessibility-audit.skill) · [dist/il-accessibility-audit.zip](dist/il-accessibility-audit.zip)

## התקנה כפלאגין ל-Claude Code / Install as a Claude Code plugin

בשורת הפקודה של Claude Code:

```
/plugin install il-accessibility-audit --marketplace jordanhemo/il-accessibility-audit
```

מאשרים (`y`) את הוספת ה-marketplace ובוחרים היקף התקנה. מהטרמינל:

```bash
claude plugin install il-accessibility-audit --marketplace jordanhemo/il-accessibility-audit
```

באפליקציית הדסקטופ: + ליד תיבת ההקלדה → Plugins → Add marketplace עם `jordanhemo/il-accessibility-audit` → Add plugin.

עדכון לגרסה חדשה: `/plugin marketplace update il-accessibility-audit`. להתקנה ב-Claude.ai, Codex וסוכנים אחרים ראו [INSTALL.md](INSTALL.md).

## מה הסקיל עושה

1. **סורק** קובצי HTML, JSX/TSX, Vue, Svelte ו-CSS (Python 3, ללא תלויות).
2. **מתקן אוטומטית** רק ממצאים שיש להם תיקון אחד נכון: `lang="he"`, `dir="rtl"`, `tabindex` חיובי.
3. **מציע פתרון** לכל מה שדורש שיקול דעת: טקסט חלופי, תוויות, ניגודיות, ARIA, מדיה אוטומטית.
4. **מתריע** כשחסרה הצהרת נגישות (חובה חוקית) ומספק תבנית.
5. **מפיק** `accessibility-report.md` עם קובץ, שורה, חומרה וסעיף WCAG לכל ממצא.

## מבנה

```
il-accessibility-audit/     the skill (copy this folder to your agent's skills directory)
  SKILL.md                  instructions for the agent
  scripts/scan.py           the scanner (also usable standalone)
  references/               legal background, accessibility statement template
AGENTS.md                   notes for agents working on this repo
INSTALL.md                  per-agent installation
```

## מגבלות

הסריקה סטטית: היא לא רואה תוכן שנוצר בזמן ריצה ולא מפענחת משתני CSS. הדוח הוא כלי עזר ואינו מחליף בדיקת נגישות מקצועית או ייעוץ משפטי.

## רישיון

MIT
