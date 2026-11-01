---
name: il-accessibility-audit
description: Scans a web project (static HTML/CSS/JS, React/Next.js, Vue, Svelte) for accessibility violations against Israeli Standard 5568 and the Israeli accessibility-for-service regulations (Takanot Negishut HaSherut, 2013), which is based on WCAG 2.0/2.1 Level AA plus Israel-specific requirements like Hebrew lang/dir="rtl" and the mandatory accessibility statement (הצהרת נגישות). Produces a detailed markdown report (file, line, severity, violated WCAG/legal criterion), auto-fixes issues that are safe and unambiguous (missing lang/dir, positive tabindex), and proposes concrete fixes for everything that needs human judgment (alt text content, labels, color contrast, accessibility statement content). Use this whenever the user asks for an accessibility audit/scan/review of a website or web app, mentions נגישות, תקן 5568, נגישות לשירות, הצהרת נגישות, WCAG compliance for an Israeli site, or asks to make a site "accessible" or "תקין לפי החוק" — even if they don't name the skill directly.
---

# IL Accessibility Audit

Audits a web project against Israeli Standard 5568 / the accessibility-for-service regulations
(itself based on WCAG 2.0/2.1 AA), produces a report, and fixes what is safe to fix automatically.

Read `references/il-accessibility-law.md` once at the start of a new audit if you are not already
familiar with the Israeli legal context — it explains *why* each rule exists (useful for writing a
report a non-technical stakeholder can act on) and maps every rule the scanner emits to its WCAG
criterion or legal basis.

## Workflow

1. **Identify the target directory.** Default to the current project unless the user names another
   path. Confirm with the user if it's ambiguous which directory/app to scan (e.g. a monorepo with
   several apps).

2. **Run the static scanner.** It is read-only — it never edits anything, only detects and reports:

   ```bash
   python3 <skill_dir>/scripts/scan.py <target_dir>
   ```

   It walks `.html`, `.htm`, `.jsx`, `.tsx`, `.vue`, `.js`, `.ts`, `.svelte`, `.css`, `.scss`, `.less`
   files (skipping `node_modules`, `.git`, `dist`, `build`, `.next`, etc.) and prints a JSON array of
   issues to stdout. Each issue has `rule`, `file`, `line`, `severity`, `wcag`, `message_he`,
   `fixable`, `suggested_fix`, and (when unambiguous) `exact_replacement: {old, new}`.

   The scanner is a heuristic, not a full browser-based audit (no real DOM, no computed styles, no
   JS-rendered content). It catches the large majority of structural/markup issues but will miss
   anything that only exists after client-side rendering or complex conditional logic. Say so in the
   report rather than implying full coverage — if the project is React/Vue-heavy with lots of logic
   in `.js`/`.ts` files building DOM dynamically (not JSX/template literals), mention that a live
   audit (e.g. a headless browser run) would catch more, and offer to do one if tooling is available.

3. **Triage each issue** into one of two buckets:

   - **`fixable: true`** — the scanner already supplies `exact_replacement`. These are safe because
     there's exactly one correct value (e.g. a Hebrew page missing `lang` can only correctly get
     `lang="he"`; a positive `tabindex` can only safely become `tabindex="0"`). Apply these directly
     with the Edit tool, file by file. After editing, mention in the report that it was fixed, not
     just flagged.
   - **`fixable: false`** — anything that requires judgment: alt text content, label wording, color
     choices, ARIA semantics, autoplay/UX tradeoffs, and the accessibility statement content. Do
     **not** guess these (e.g. don't invent `alt="תמונה"` — a meaningless alt is arguably worse than
     none, since it passes automated checks while still failing the user). Put `message_he` and
     `suggested_fix` into the report instead so a human (or you, once given more context) can decide.

   The one exception worth a special pass: `missing-accessibility-statement`. This is a legal
   requirement, not just a UX nicety, so don't just mention it in passing — call it out prominently
   near the top of the report. Offer to generate the page from
   `references/accessibility-statement-template.md`, but only actually create it if the user gives
   you (or confirms you should use placeholder) the accessibility coordinator's name/contact details —
   content in a legal disclosure shouldn't be invented.

4. **Write the report.** Save it as `accessibility-report.md` in the target project (ask first if a
   file by that name already exists and isn't yours). Structure:

   ```markdown
   # דוח נגישות — <project name> (ת"י 5568 / WCAG 2.0-2.1 AA)
   תאריך: <today>
   נסקרו: <N> קבצים | נמצאו: <N> ממצאים | תוקנו אוטומטית: <N>

   ## סיכום לפי חוק
   <one paragraph: is there an accessibility statement? is this likely in violation of the
   2013 regulations right now? keep it plain-language, this section is for a site owner, not a dev>

   ## ממצאים קריטיים (חוקיים/משפיעים מאוד על משתמשים)
   | קובץ:שורה | כלל | WCAG | תיאור | סטטוס |
   |---|---|---|---|---|
   ...one row per issue, grouped by severity (critical, serious, moderate, minor)...

   ## תוקן אוטומטית
   <list what you changed and in which files>

   ## דורש החלטה אנושית
   <for each non-fixable issue: file:line, what's wrong, and the concrete suggested_fix text>

   ## הצהרת נגישות
   <status + next step>
   ```

   Keep severities grouped and sorted critical → minor within each group so the reader fixes the
   highest-impact things first. Translate `message_he`/`suggested_fix` as-is (already Hebrew) —
   don't re-translate to English unless the user is working in English.

5. **Tell the user what you did and what's left**, pointing at the report file and summarizing the
   counts (e.g. "מצאתי 17 ממצאים, תיקנתי 4 אוטומטית, 13 דורשים החלטה — כולל חובה חוקית: לא נמצאה הצהרת נגישות").

## Notes on judgment calls

- **Don't auto-fix `img-missing-alt` by guessing content.** If the surrounding code/filename makes
  the content obvious (e.g. `alt` clearly describes a UI icon whose purpose is stated in a nearby
  `aria-label` or button text), you may propose specific alt text in the report — but still list it
  under "requires a decision" rather than silently editing, since you're inferring, not reading a
  spec. If the user explicitly asks you to fill in your best-guess alt text across the board, that's
  a different, explicit request — you can do it, but say in the report which ones were inferred so a
  human can double check them.
- **Low-contrast findings are a starting point, not a verdict.** The CSS scan only catches
  `color`/`background-color` pairs declared together in the same rule block with literal values —
  it can't resolve CSS variables, inherited backgrounds, or cascade order. Say this limitation
  explicitly if the project uses design tokens/CSS variables heavily, since the scanner will
  under-report in that case, not over-report.
- **Re-run the scanner after fixes** to confirm the fixable issues are gone and get a clean final
  count for the report.
- If the user wants a one-off check rather than a full project audit (e.g. "is this one page okay?"),
  you can run the scanner against a single file or subdirectory — it works the same way.
