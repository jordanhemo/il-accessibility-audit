# בודק נגישות ישראלי ל-Claude

סקיל ל-Claude שסורק פרויקט אינטרנט לפי **תקן ישראלי 5568** ו**תקנות נגישות השירות (תשע"ג-2013)**, מפיק דוח בעברית ומתקן אוטומטית את מה שבטוח לתקן.

**דף הסקיל והורדה:** https://jordanhemo.github.io/il-accessibility-audit/

הדף נמצא בתיקיית `docs/` ומוכן לפריסה גם ב-Vercel: מייבאים את הריפו ב-[vercel.com/new](https://vercel.com/new), משאירים Framework Preset על "Other" ולוחצים Deploy. קובץ `vercel.json` כבר מגדיר את `docs/` כתיקיית הפלט.

## מה הסקיל עושה

1. **סורק** קובצי HTML, ‏JSX/TSX, ‏Vue, ‏Svelte ו-CSS עם סקריפט קריאה-בלבד (Python 3, ללא תלויות).
2. **מתקן אוטומטית** רק ממצאים שיש להם תיקון אחד נכון: `lang="he"`, ‏`dir="rtl"`, ‏`tabindex` חיובי.
3. **מציע פתרון** לכל מה שדורש שיקול דעת: טקסט חלופי, תוויות לטפסים, ניגודיות צבעים, ARIA, מדיה אוטומטית.
4. **מתריע** כשחסרה הצהרת נגישות (חובה חוקית) ומספק תבנית.
5. **מפיק** קובץ `accessibility-report.md` עם קובץ, שורה, חומרה וסעיף WCAG לכל ממצא.

## התקנה

**Claude.ai / אפליקציית Claude:** מורידים את [`docs/il-accessibility-audit.skill`](docs/il-accessibility-audit.skill) ומעלים אותו בהגדרות, בחלק של הסקילים.

**Claude Code:**

```bash
git clone https://github.com/jordanhemo/il-accessibility-audit.git
cp -r il-accessibility-audit/il-accessibility-audit ~/.claude/skills/
```

## שימוש

כותבים ל-Claude בשפה חופשית, למשל:

> תבדוק אם האתר בתיקייה הזו עומד בתקן הנגישות הישראלי ותתקן מה שאפשר

אפשר גם להריץ את הסורק לבד:

```bash
python3 il-accessibility-audit/scripts/scan.py path/to/project
```

## מבנה

```
il-accessibility-audit/      הסקיל עצמו
  SKILL.md                   הנחיות ל-Claude
  scripts/scan.py            הסורק
  references/                רקע משפטי ותבנית הצהרת נגישות
docs/                        דף הנחיתה (GitHub Pages) וקובץ ההורדה
```

## מגבלות

הסריקה סטטית: היא לא רואה תוכן שנוצר בזמן ריצה ולא מפענחת משתני CSS. הדוח הוא כלי עזר ואינו מחליף בדיקת נגישות מקצועית או ייעוץ משפטי.

## משוב

נשמח לדיווחים על ממצאים שגויים, בדיקות חסרות או רעיונות דרך [Issues](https://github.com/jordanhemo/il-accessibility-audit/issues).

## רישיון

MIT
