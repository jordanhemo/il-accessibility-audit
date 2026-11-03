---
name: il-accessibility-audit
description: Scans a web project (static HTML/CSS/JS, React/Next.js, Vue, Svelte) for accessibility violations against Israeli Standard 5568 and the Israeli accessibility-for-service regulations (Takanot Negishut HaSherut, 2013), which is based on WCAG 2.0/2.1 Level AA plus Israel-specific requirements like Hebrew lang/dir="rtl" and the mandatory accessibility statement (הצהרת נגישות). Produces a detailed Hebrew markdown report (file, line, severity, violated WCAG/legal criterion), auto-fixes issues that are safe and unambiguous (missing lang/dir, positive tabindex), and proposes concrete fixes for everything that needs human judgment (alt text content, labels, color contrast, accessibility statement content). Use this whenever the user asks for an accessibility audit/scan/review of a website or web app, mentions נגישות, תקן 5568, נגישות לשירות, הצהרת נגישות, WCAG compliance for an Israeli site, or asks to make a site "accessible" or "תקין לפי החוק" — even if they don't name the skill directly.
---

# IL Accessibility Audit

Audits a web project against Israeli Standard 5568 / the accessibility-for-service regulations
(itself based on WCAG 2.0/2.1 AA), writes a Hebrew report, and fixes what is safe to fix.

This skill works with any coding agent that can run a shell command and edit files (Claude Code,
Claude.ai, Codex CLI, Cursor, Gemini CLI and similar). All paths below are relative to the
directory that contains this SKILL.md.

Read `references/il-accessibility-law.md` once at the start of a new audit if you are not already
familiar with the Israeli legal context. It explains *why* each rule exists, which is what makes
the report useful to a site owner rather than just a developer, and maps every rule the scanner
emits to its WCAG criterion or legal basis.

## Workflow

1. **Identify the target directory.** Default to the current project unless the user names another
   path. If it's ambiguous which app to scan (a monorepo with several apps), ask.

2. **Run the scanner with fixes and a report.** Requires Python 3, no packages:

   ```bash
   python3 scripts/scan.py <target_dir> --format md --fix --report <target_dir>/accessibility-report.md
   ```

   What this does:
   - Walks `.html`, `.htm`, `.jsx`, `.tsx`, `.vue`, `.js`, `.ts`, `.svelte`, `.css`, `.scss`, `.less`
     files, skipping `node_modules`, `.git`, `dist`, `build`, `.next` and similar.
   - `--fix` applies only the fixes that have exactly one correct answer: a Hebrew page missing
     `lang` gets `lang="he" dir="rtl"`, a positive `tabindex` becomes `tabindex="0"`. Nothing else
     is edited. Without `--fix` the scanner is read-only.
   - `--report` writes the Hebrew markdown report (summary by law, table of all findings grouped by
     severity, what was fixed, what needs a human decision, accessibility statement status).
   - `--format json` (the default) prints the raw findings instead, useful when you want to
     process them yourself.

   If a file named `accessibility-report.md` already exists in the project and isn't from a previous
   run of this skill, ask before overwriting it.

3. **Read the report and handle the "requires a human decision" section.** These are findings
   that need content or design judgment: alt text, label wording, color choices, ARIA semantics,
   autoplay tradeoffs, and the accessibility statement. Do not guess these. A meaningless
   `alt="תמונה"` is arguably worse than no alt, because it passes automated checks while still
   failing the user. For each one, either ask the user for the missing information or leave the
   suggested fix in the report for them to act on.

   Where the surrounding code makes the answer obvious (a close-button icon whose purpose is stated
   in nearby text), you may propose specific text in your reply, but mark it as inferred so a human
   can check it. If the user explicitly asks you to fill in best-guess alt text across the board,
   do it and list which ones were inferred.

4. **Treat a missing accessibility statement as the headline.** It is a legal requirement, not a UX
   nicety, so say so prominently. Offer to generate the page from
   `references/accessibility-statement-template.md`, but only create it once the user gives you (or
   confirms placeholders for) the accessibility coordinator's name and contact details. Content in
   a legal disclosure shouldn't be invented.

5. **Re-run the scanner without `--fix`** to confirm the fixed findings are gone, then tell the user
   where the report is and summarize the counts, for example:
   "מצאתי 17 ממצאים, תיקנתי 3 אוטומטית, 14 דורשים החלטה, כולל חובה חוקית: לא נמצאה הצהרת נגישות."

## Limits to state in the report

The scanner is static. It reads source files, not a rendered DOM, so it misses anything that only
exists after client-side rendering or inside dynamic logic that builds markup from strings. The CSS
contrast check only catches `color`/`background-color` pairs declared together with literal values;
it cannot resolve CSS variables, inherited backgrounds or cascade order, so on a design-token-heavy
project it under-reports. Say this plainly rather than implying full coverage, and offer a live
browser-based audit if that tooling is available to you.

For a one-off check ("is this one page okay?") run the scanner against a single file or
subdirectory; it works the same way.
