#!/usr/bin/env python3
"""
Static accessibility scanner for Israeli Standard 5568 / WCAG 2.0-2.1 AA compliance.
Works with any AI agent or on its own: read-only by default, emits JSON or a
Hebrew markdown report, and with --fix applies the few unambiguous fixes itself.

Usage:
    python3 scan.py <project_dir>                      # JSON issues on stdout
    python3 scan.py <project_dir> --format md          # markdown report on stdout
    python3 scan.py <project_dir> --format md --fix --report accessibility-report.md
    options: [--ext html,jsx,tsx,vue,js,ts] [--skip node_modules,dist,build,.git]

Each issue:
{
  "rule": "img-missing-alt",
  "file": "src/Hero.jsx",
  "line": 42,
  "severity": "serious" | "critical" | "moderate" | "minor",
  "wcag": "1.1.1",
  "message_he": "...",
  "fixable": true|false,
  "suggested_fix": "...",          # human-readable guidance
  "exact_replacement": {"old": "...", "new": "..."}  # present only when fixable and unambiguous
  "snippet": "..."
}
"""
import argparse
import html.parser
import json
import os
import re
import sys

SCAN_EXTENSIONS = {".html", ".htm", ".jsx", ".tsx", ".vue", ".js", ".ts", ".svelte"}
DEFAULT_SKIP_DIRS = {"node_modules", ".git", "dist", "build", ".next", "out", "coverage", ".svelte-kit", "vendor"}

VALID_ARIA_ROLES = {
    "alert", "alertdialog", "application", "article", "banner", "button", "cell", "checkbox",
    "columnheader", "combobox", "complementary", "contentinfo", "definition", "dialog",
    "directory", "document", "feed", "figure", "form", "grid", "gridcell", "group", "heading",
    "img", "link", "list", "listbox", "listitem", "log", "main", "marquee", "math", "menu",
    "menubar", "menuitem", "menuitemcheckbox", "menuitemradio", "navigation", "none", "note",
    "option", "presentation", "progressbar", "radio", "radiogroup", "region", "row",
    "rowgroup", "rowheader", "scrollbar", "search", "searchbox", "separator", "slider",
    "spinbutton", "status", "switch", "tab", "table", "tablist", "tabpanel", "term",
    "textbox", "timer", "toolbar", "tooltip", "tree", "treegrid", "treeitem",
}

HEADING_RE = re.compile(r"^h([1-6])$")
SKIP_LINK_TEXT_RE = re.compile(r"(דלג|skip)", re.IGNORECASE)
STATEMENT_HINT_RE = re.compile(r"(הצהרת\s*נגישות|accessibility[-_ ]?statement)", re.IGNORECASE)
DECORATIVE_HINT_RE = re.compile(r"(icon|logo|deco|spacer|bg[-_]|background|divider|separator)", re.IGNORECASE)

TABINDEX_RE = re.compile(r"tab[Ii]ndex\s*=\s*[\"'{]?\s*(\d+)\s*[}\"']?")
AUTOPLAY_RE = re.compile(r"\bautoplay\b|\bautoPlay\b", re.IGNORECASE)
MUTED_RE = re.compile(r"\bmuted\b", re.IGNORECASE)


def wcag_contrast_ratio(rgb1, rgb2):
    def luminance(rgb):
        def chan(c):
            c = c / 255.0
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
        r, g, b = (chan(c) for c in rgb)
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    l1, l2 = luminance(rgb1), luminance(rgb2)
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def parse_color(value):
    value = value.strip()
    m = re.match(r"^#([0-9a-fA-F]{3})$", value)
    if m:
        h = m.group(1)
        return tuple(int(c * 2, 16) for c in h)
    m = re.match(r"^#([0-9a-fA-F]{6})$", value)
    if m:
        h = m.group(1)
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    m = re.match(r"^rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)", value)
    if m:
        return tuple(int(m.group(i)) for i in (1, 2, 3))
    return None


def scan_css_contrast(text, filename, issues):
    for block_match in re.finditer(r"([^{}]+)\{([^{}]*)\}", text):
        selector, body = block_match.groups()
        color_m = re.search(r"(?<!background-)(?<!border-)color\s*:\s*([^;]+);", body)
        bg_m = re.search(r"background(?:-color)?\s*:\s*([^;]+);", body)
        if not color_m or not bg_m:
            continue
        c1, c2 = parse_color(color_m.group(1)), parse_color(bg_m.group(1))
        if not c1 or not c2:
            continue
        ratio = wcag_contrast_ratio(c1, c2)
        size_m = re.search(r"font-size\s*:\s*([\d.]+)(px|pt|rem|em)", body)
        weight_m = re.search(r"font-weight\s*:\s*(bold|[6-9]00)", body, re.IGNORECASE)
        is_large = False
        if size_m:
            size, unit = float(size_m.group(1)), size_m.group(2)
            px = size * 16 if unit in ("rem", "em") else (size * 1.333 if unit == "pt" else size)
            if px >= 24 or (px >= 18.66 and weight_m):
                is_large = True
        threshold = 3.0 if is_large else 4.5
        if ratio < threshold:
            line = text[: block_match.start()].count("\n") + 1
            issues.append({
                "rule": "low-contrast",
                "file": filename,
                "line": line,
                "severity": "serious",
                "wcag": "1.4.3",
                "message_he": f"ניגודיות {ratio:.2f}:1 בין צבע טקסט לרקע בסלקטור '{selector.strip()}', מתחת לסף הנדרש ({threshold}:1).",
                "fixable": False,
                "suggested_fix": f"הכהה/הבהה את אחד הצבעים כך שהניגודיות תעלה ל-{threshold}:1 ומעלה. יש לבדוק עם כלי ניגודיות (למשל WebAIM Contrast Checker) כדי לשמור על זהות המותג.",
                "exact_replacement": None,
                "snippet": block_match.group(0).strip()[:200],
            })


class A11yHTMLParser(html.parser.HTMLParser):
    def __init__(self, filename, lines, issues, is_full_document_candidate):
        super().__init__(convert_charrefs=True)
        self.filename = filename
        self.lines = lines
        self.issues = issues
        self.is_full_document_candidate = is_full_document_candidate
        self.tag_stack = []
        self.label_for_ids = set()
        self.label_wraps_input = False
        self.headings = []  # (level, line)
        self.h1_count = 0
        self.found_html_tag = False
        self.found_skip_link = False
        self.found_main = False
        self.found_nav = False
        self.current_text_buffer = []
        self.text_capture_stack = []  # stack of (tag, start_index_in_buffer)
        self.last_anchor_href = None

    def line_of(self):
        return self.getpos()[0]

    def snippet_at(self):
        ln = self.line_of()
        if 1 <= ln <= len(self.lines):
            return self.lines[ln - 1].strip()[:200]
        return ""

    def get_attr(self, attrs, *names):
        d = {k.lower(): v for k, v in attrs}
        for n in names:
            if n.lower() in d:
                return d[n.lower()]
        return None

    def handle_starttag(self, tag, attrs):
        self._handle_tag(tag, attrs, self_closing=False)

    def handle_startendtag(self, tag, attrs):
        self._handle_tag(tag, attrs, self_closing=True)

    def _handle_tag(self, tag, attrs, self_closing):
        tlow = tag.lower()
        line = self.line_of()
        d = {k.lower(): v for k, v in attrs}

        if tlow == "html":
            self.found_html_tag = True
            lang = d.get("lang")
            if not lang:
                self.issues.append({
                    "rule": "missing-lang", "file": self.filename, "line": line,
                    "severity": "serious", "wcag": "3.1.1",
                    "message_he": "לתג <html> אין מאפיין lang. קורא מסך לא יידע לבחור מנגנון הגייה/ניקוד נכון.",
                    "fixable": True,
                    "suggested_fix": 'הוסף lang="he" dir="rtl" לתג <html>.',
                    "exact_replacement": {"old": "<html", "new": '<html lang="he" dir="rtl"'} if "dir" not in d else {"old": "<html", "new": '<html lang="he"'},
                    "snippet": self.snippet_at(),
                })
            elif lang.lower().startswith("he"):
                dir_attr = d.get("dir")
                if not dir_attr or dir_attr.lower() != "rtl":
                    self.issues.append({
                        "rule": "missing-dir", "file": self.filename, "line": line,
                        "severity": "serious", "wcag": "ישראלי (לא WCAG גנרי)",
                        "message_he": 'עמוד בעברית (lang="he") אך לתג <html> אין dir="rtl". מסך הצגה בכיווניות שגויה.',
                        "fixable": True,
                        "suggested_fix": 'הוסף dir="rtl" לתג <html>.',
                        "exact_replacement": {"old": f'lang="{lang}"', "new": f'lang="{lang}" dir="rtl"'} if not dir_attr else None,
                        "snippet": self.snippet_at(),
                    })

        if tlow in ("img", "image"):
            alt = d.get("alt")
            src = d.get("src") or d.get("srcset") or ""
            if alt is None:
                self.issues.append({
                    "rule": "img-missing-alt", "file": self.filename, "line": line,
                    "severity": "critical", "wcag": "1.1.1",
                    "message_he": f"תמונה ללא מאפיין alt (src: {src[:60]}).",
                    "fixable": False,
                    "suggested_fix": 'הוסף alt="<תיאור עברי קצר של התמונה>". אם התמונה דקורטיבית בלבד, הוסף alt="" במפורש.',
                    "exact_replacement": None,
                    "snippet": self.snippet_at(),
                })
            elif alt.strip() == "" and not DECORATIVE_HINT_RE.search(src) and not DECORATIVE_HINT_RE.search(d.get("class") or ""):
                self.issues.append({
                    "rule": "img-empty-alt-informative", "file": self.filename, "line": line,
                    "severity": "moderate", "wcag": "1.1.1",
                    "message_he": f"alt=\"\" על תמונה שלא נראית דקורטיבית (src: {src[:60]}). בדוק אם התמונה אכן דקורטיבית.",
                    "fixable": False,
                    "suggested_fix": "אם התמונה נושאת מידע, הוסף תיאור עברי קצר ב-alt. אם היא דקורטיבית בלבד, השאר alt=\"\" (תקין).",
                    "exact_replacement": None,
                    "snippet": self.snippet_at(),
                })

        if tlow == "label":
            fr = d.get("for")
            if fr:
                self.label_for_ids.add(fr)
            self.text_capture_stack.append(("label", None))

        if tlow in ("input", "textarea", "select"):
            itype = (d.get("type") or "").lower()
            if itype not in ("hidden", "submit", "button", "reset", "image"):
                has_aria = d.get("aria-label") or d.get("aria-labelledby") or d.get("title")
                elem_id = d.get("id")
                inside_label = any(t == "label" for t, _ in self.text_capture_stack)
                if not has_aria and not inside_label and (not elem_id or elem_id not in self.label_for_ids):
                    self.issues.append({
                        "rule": "input-missing-label", "file": self.filename, "line": line,
                        "severity": "critical", "wcag": "1.3.1 / 4.1.2",
                        "message_he": f"שדה <{tlow}> (type={itype or 'text'}) ללא תווית מקושרת (label/aria-label/aria-labelledby).",
                        "fixable": False,
                        "suggested_fix": '<label for="...">טקסט תיאורי בעברית</label> המקושר ל-id של השדה, או aria-label ישירות על השדה.',
                        "exact_replacement": None,
                        "snippet": self.snippet_at(),
                    })

        hm = HEADING_RE.match(tlow)
        if hm:
            level = int(hm.group(1))
            self.headings.append((level, line))
            if level == 1:
                self.h1_count += 1

        if tlow == "main":
            self.found_main = True
        if tlow == "nav":
            self.found_nav = True

        if tlow == "a":
            href = d.get("href") or ""
            self.last_anchor_href = href
            if href.startswith("#") and (d.get("aria-label") or "")[:0] == "":
                pass  # text checked at close/next text events
            self.text_capture_stack.append(("a", {"href": href, "aria": d.get("aria-label"), "line": line}))
        elif tlow == "button":
            self.text_capture_stack.append(("button", {"aria": d.get("aria-label"), "line": line}))

        role = d.get("role")
        if role and role.lower() not in VALID_ARIA_ROLES:
            self.issues.append({
                "rule": "aria-invalid-role", "file": self.filename, "line": line,
                "severity": "moderate", "wcag": "4.1.2",
                "message_he": f'role="{role}" אינו תפקיד ARIA מוכר/תקין.',
                "fixable": False,
                "suggested_fix": "בדוק את רשימת התפקידים התקנית ב-WAI-ARIA והחלף לתפקיד המתאים, או הסר אם אינו נדרש.",
                "exact_replacement": None,
                "snippet": self.snippet_at(),
            })

        tabindex_raw = d.get("tabindex")
        if tabindex_raw:
            m = TABINDEX_RE.search(f'tabindex="{tabindex_raw}"')
            try:
                val = int(re.sub(r"[^\d-]", "", tabindex_raw))
            except ValueError:
                val = None
            if val is not None and val > 0:
                self.issues.append({
                    "rule": "positive-tabindex", "file": self.filename, "line": line,
                    "severity": "moderate", "wcag": "2.4.3",
                    "message_he": f'tabindex="{val}" חיובי שובר את סדר הטאב הטבעי של הדף.',
                    "fixable": True,
                    "suggested_fix": 'החלף לתabindex="0" (נגיש ללא שינוי סדר) או הסר את המאפיין אם אינו נחוץ.',
                    "exact_replacement": {"old": f'tabindex="{tabindex_raw}"', "new": 'tabindex="0"'},
                    "snippet": self.snippet_at(),
                })

        if tlow in ("video", "audio"):
            autoplay = "autoplay" in d
            muted = "muted" in d
            if autoplay and not muted:
                self.issues.append({
                    "rule": "autoplay-media", "file": self.filename, "line": line,
                    "severity": "serious", "wcag": "1.4.2",
                    "message_he": f"<{tlow}> עם autoplay ובלי muted — מדיה שמתחילה לבד עם קול פוגעת במשתמשי קוראי מסך.",
                    "fixable": False,
                    "suggested_fix": "הוסף muted, או הסר autoplay והצג כפתור הפעלה ברור, ותמיד הוסף controls.",
                    "exact_replacement": None,
                    "snippet": self.snippet_at(),
                })

        if not self_closing and tlow not in ("img", "input", "br", "hr", "meta", "link"):
            self.tag_stack.append(tlow)

    def handle_data(self, data):
        if self.text_capture_stack:
            tag, info = self.text_capture_stack[-1]
            if info is not None:
                info.setdefault("text", "")
                info["text"] += data
        if self.found_html_tag and SKIP_LINK_TEXT_RE.search(data) and self.last_anchor_href and self.last_anchor_href.startswith("#"):
            self.found_skip_link = True

    def handle_endtag(self, tag):
        tlow = tag.lower()
        if self.tag_stack and self.tag_stack[-1] == tlow:
            self.tag_stack.pop()
        if tlow in ("a", "button", "label") and self.text_capture_stack and self.text_capture_stack[-1][0] == tlow:
            entry = self.text_capture_stack.pop()
            if tlow in ("a", "button"):
                _, info = entry
                text = (info.get("text") or "").strip()
                has_aria = info.get("aria")
                if not text and not has_aria:
                    self.issues.append({
                        "rule": "link-no-discernible-text", "file": self.filename, "line": info["line"],
                        "severity": "serious", "wcag": "2.4.4 / 4.1.2",
                        "message_he": f"<{tlow}> ללא טקסט נגיש (ריק, ייתכן שמכיל רק אייקון) וללא aria-label.",
                        "fixable": False,
                        "suggested_fix": 'הוסף aria-label="<פעולה בעברית>" (למשל aria-label="סגור") או טקסט גלוי.',
                        "exact_replacement": None,
                        "snippet": "",
                    })

    def finalize(self, issues):
        if self.h1_count == 0 and self.is_full_document_candidate and self.found_html_tag:
            issues.append({
                "rule": "missing-h1", "file": self.filename, "line": 1,
                "severity": "moderate", "wcag": "1.3.1",
                "message_he": "לא נמצאה כותרת <h1> בעמוד.",
                "fixable": False,
                "suggested_fix": "הוסף כותרת <h1> אחת שמתארת את תוכן העמוד.",
                "exact_replacement": None, "snippet": "",
            })
        if self.h1_count > 1:
            issues.append({
                "rule": "multiple-h1", "file": self.filename, "line": 1,
                "severity": "minor", "wcag": "1.3.1",
                "message_he": f"נמצאו {self.h1_count} תגי <h1> בעמוד אחד.",
                "fixable": False,
                "suggested_fix": "השתמש ב-h1 יחיד לעמוד, ובכותרות משנה (h2 ואילך) לשאר המבנה.",
                "exact_replacement": None, "snippet": "",
            })
        prev_level = None
        for level, line in self.headings:
            if prev_level is not None and level > prev_level + 1:
                issues.append({
                    "rule": "heading-order-skip", "file": self.filename, "line": line,
                    "severity": "minor", "wcag": "1.3.1",
                    "message_he": f"דילוג בהיררכיית הכותרות: מ-h{prev_level} ישר ל-h{level}.",
                    "fixable": False,
                    "suggested_fix": f"השתמש ב-h{prev_level + 1} במקום h{level}, או הוסף רמת כותרת חסרה.",
                    "exact_replacement": None, "snippet": "",
                })
            prev_level = level


def extract_vue_template(text):
    m = re.search(r"<template[^>]*>(.*)</template>", text, re.DOTALL)
    return m.group(1) if m else text


def should_skip_dir(dirname, skip_dirs):
    return dirname in skip_dirs or dirname.startswith(".")


def collect_files(root, extensions, skip_dirs):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not should_skip_dir(d, skip_dirs)]
        for fn in filenames:
            if os.path.splitext(fn)[1].lower() in extensions:
                yield os.path.join(dirpath, fn)


def scan_file(path, root, issues, skip_link_tracker):
    rel = os.path.relpath(path, root)
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
    except OSError:
        return
    lines = text.splitlines()

    ext = os.path.splitext(path)[1].lower()
    parse_target = text
    is_full_doc_candidate = "<html" in text.lower() or ext in (".html", ".htm")
    if ext == ".vue":
        parse_target = extract_vue_template(text)
        is_full_doc_candidate = "<html" in text.lower()

    parser = A11yHTMLParser(rel, lines, issues, is_full_doc_candidate)
    try:
        parser.feed(parse_target)
        parser.close()
    except Exception:
        pass
    parser.finalize(issues)

    if ext in (".css", ".scss", ".less"):
        scan_css_contrast(text, rel, issues)

    if is_full_doc_candidate:
        skip_link_tracker["candidate_files"].append(rel)
        if parser.found_skip_link:
            skip_link_tracker["found_any"] = True


def scan_project_for_statement(root, extensions, skip_dirs, issues):
    found = False
    for path in collect_files(root, extensions | {".md"}, skip_dirs):
        if os.path.basename(path) == "accessibility-report.md":
            continue
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()
        except OSError:
            continue
        if STATEMENT_HINT_RE.search(text):
            found = True
            break
    if not found:
        issues.append({
            "rule": "missing-accessibility-statement", "file": "<project>", "line": 0,
            "severity": "critical", "wcag": "חוקי ישראלי (תקנות נגישות לשירות, תשע\"ג-2013)",
            "message_he": "לא נמצאה 'הצהרת נגישות' בפרויקט. החוק הישראלי מחייב כל אתר שירות לפרסם הצהרת נגישות מקושרת מכל עמוד.",
            "fixable": False,
            "suggested_fix": "ראה references/accessibility-statement-template.md בסקיל ליצירת דף הצהרת נגישות, וקשר אותו מהפוטר בכל עמוד.",
            "exact_replacement": None, "snippet": "",
        })


SEVERITY_ORDER = ["critical", "serious", "moderate", "minor"]
SEVERITY_HE = {"critical": "קריטי", "serious": "חמור", "moderate": "בינוני", "minor": "קל"}


def apply_fixes(root, issues):
    """Apply every exact_replacement once per file. Returns the issues that were fixed."""
    fixed = []
    by_file = {}
    for issue in issues:
        if issue.get("fixable") and issue.get("exact_replacement"):
            by_file.setdefault(issue["file"], []).append(issue)
    for rel, file_issues in by_file.items():
        path = os.path.join(root, rel)
        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
        except (OSError, UnicodeDecodeError):
            continue
        original = text
        for issue in file_issues:
            old, new = issue["exact_replacement"]["old"], issue["exact_replacement"]["new"]
            if text.count(old) == 1:
                text = text.replace(old, new)
                issue["status"] = "fixed"
                fixed.append(issue)
            elif old in text and issue["rule"] == "positive-tabindex":
                text = text.replace(old, new)
                issue["status"] = "fixed"
                fixed.append(issue)
        if text != original:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
    return fixed


def render_markdown(root, issues, file_count, fixed):
    import datetime
    fixed_ids = {id(i) for i in fixed}
    open_issues = [i for i in issues if id(i) not in fixed_ids]
    statement_missing = any(i["rule"] == "missing-accessibility-statement" for i in issues)
    critical_open = sum(1 for i in open_issues if i["severity"] == "critical")
    out = []
    out.append(f"# דוח נגישות — {os.path.basename(root) or root} (ת\"י 5568 / WCAG 2.0-2.1 AA)")
    out.append(f"תאריך: {datetime.date.today().isoformat()}  ")
    out.append(f"נסרקו: {file_count} קבצים | נמצאו: {len(issues)} ממצאים | תוקנו אוטומטית: {len(fixed)} | פתוחים: {len(open_issues)}")
    out.append("")
    out.append("## סיכום לפי חוק")
    if statement_missing:
        out.append("**לא נמצאה הצהרת נגישות בפרויקט.** תקנות נגישות השירות (תשע\"ג-2013) מחייבות כל אתר שנותן שירות לציבור לפרסם הצהרת נגישות המקושרת מכל עמוד. כל עוד היא חסרה, האתר אינו עומד בדרישות החוק גם אם שאר הממצאים יתוקנו.")
    else:
        out.append("נמצאה התייחסות להצהרת נגישות בפרויקט. יש לוודא שהיא מקושרת מכל עמוד ומכילה את פרטי רכז הנגישות ותאריך עדכון.")
    if critical_open:
        out.append(f"נותרו {critical_open} ממצאים קריטיים שדורשים טיפול לפני שניתן להצהיר על עמידה בתקן.")
    elif not open_issues:
        out.append("לא נותרו ממצאים פתוחים בסריקה הסטטית.")
    out.append("")
    out.append("הסריקה סטטית: היא בודקת את קוד המקור ולא תוכן שנוצר בזמן ריצה, ואינה מפענחת משתני CSS. הדוח הוא כלי עזר ואינו מחליף בדיקת נגישות מקצועית או ייעוץ משפטי.")
    out.append("")
    out.append("## כל הממצאים")
    out.append("| חומרה | קובץ:שורה | כלל | WCAG | תיאור | סטטוס |")
    out.append("|---|---|---|---|---|---|")
    ordered = sorted(issues, key=lambda i: (SEVERITY_ORDER.index(i["severity"]), i["file"], i["line"]))
    for i in ordered:
        loc = f"`{i['file']}:{i['line']}`" if i["line"] else f"`{i['file']}`"
        status = "תוקן" if id(i) in fixed_ids else ("ניתן לתיקון אוטומטי" if i.get("fixable") else "דורש החלטה")
        desc = i["message_he"].replace("|", "\\|")
        out.append(f"| {SEVERITY_HE[i['severity']]} | {loc} | `{i['rule']}` | {i['wcag']} | {desc} | {status} |")
    out.append("")
    out.append("## תוקן אוטומטית")
    if fixed:
        for i in fixed:
            r = i["exact_replacement"]
            out.append(f"- `{i['file']}:{i['line']}` — `{r['old']}` → `{r['new']}`")
    else:
        out.append("לא בוצעו תיקונים אוטומטיים (הרץ עם `--fix` כדי ליישם את התיקונים החד-משמעיים).")
    out.append("")
    out.append("## דורש החלטה אנושית")
    decisions = [i for i in open_issues if not i.get("fixable")]
    if decisions:
        for i in sorted(decisions, key=lambda i: (SEVERITY_ORDER.index(i["severity"]), i["file"], i["line"])):
            loc = f"`{i['file']}:{i['line']}`" if i["line"] else f"`{i['file']}`"
            out.append(f"### {loc} — {i['rule']} ({SEVERITY_HE[i['severity']]})")
            out.append(i["message_he"])
            out.append("")
            out.append(f"**פתרון מוצע:** {i['suggested_fix']}")
            if i.get("snippet"):
                out.append("")
                out.append("```")
                out.append(i["snippet"])
                out.append("```")
            out.append("")
    else:
        out.append("אין.")
        out.append("")
    out.append("## הצהרת נגישות")
    if statement_missing:
        out.append("חסרה. יש ליצור דף הצהרת נגישות (תבנית ב-`references/accessibility-statement-template.md` של הסקיל), למלא את פרטי רכז הנגישות ותאריך העדכון, ולקשר אליו מהפוטר בכל עמוד. אין למלא פרטים אלה בניחוש.")
    else:
        out.append("נמצאה. יש לוודא שהתוכן מעודכן ותואם לממצאי הסריקה הנוכחית.")
    out.append("")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project_dir")
    ap.add_argument("--ext", default=",".join(e.lstrip(".") for e in SCAN_EXTENSIONS))
    ap.add_argument("--skip", default=",".join(DEFAULT_SKIP_DIRS))
    ap.add_argument("--format", choices=["json", "md"], default="json")
    ap.add_argument("--fix", action="store_true", help="apply the unambiguous fixes (lang, dir, tabindex) in place")
    ap.add_argument("--report", help="also write the markdown report to this path")
    args = ap.parse_args()

    extensions = {f".{e.strip().lstrip('.')}" for e in args.ext.split(",") if e.strip()}
    skip_dirs = {d.strip() for d in args.skip.split(",") if d.strip()}
    root = os.path.abspath(args.project_dir)

    issues = []
    html_like = {e for e in extensions if e != ".css" and e != ".scss" and e != ".less"} | {".css", ".scss", ".less"}
    skip_link_tracker = {"candidate_files": [], "found_any": False}
    file_count = 0
    for path in collect_files(root, html_like, skip_dirs):
        file_count += 1
        scan_file(path, root, issues, skip_link_tracker)

    scan_project_for_statement(root, extensions, skip_dirs, issues)

    if skip_link_tracker["candidate_files"] and not skip_link_tracker["found_any"]:
        issues.append({
            "rule": "missing-skip-link", "file": skip_link_tracker["candidate_files"][0], "line": 1,
            "severity": "moderate", "wcag": "2.4.1",
            "message_he": "לא נמצא קישור 'דלג לתוכן' (skip link) באף אחד מהקבצים שנסרקו בפרויקט.",
            "fixable": False,
            "suggested_fix": 'הוסף בתחילת ה-body/layout הראשי: <a href="#main" class="skip-link">דלג לתוכן העמוד</a> ו-id="main" על אזור התוכן הראשי.',
            "exact_replacement": None, "snippet": "",
        })

    fixed = apply_fixes(root, issues) if args.fix else []
    for i in issues:
        i.setdefault("status", "open")

    if args.format == "md" or args.report:
        report = render_markdown(root, issues, file_count, fixed)
        if args.report:
            with open(args.report, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"report written to {args.report}", file=sys.stderr)
    if args.format == "md":
        print(report)
    else:
        print(json.dumps(issues, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
