# Agent instructions

This repository is an **agent skill** that audits web projects for Israeli accessibility law
(Israeli Standard 5568, based on WCAG 2.0/2.1 AA). It has no build step and no dependencies
beyond Python 3.

- The skill lives in `il-accessibility-audit/`. Its entry point for you is
  `il-accessibility-audit/SKILL.md`; read it before using the skill.
- The scanner is `il-accessibility-audit/scripts/scan.py`. Typical use on a target project:

  ```bash
  python3 il-accessibility-audit/scripts/scan.py <project_dir> --format md --fix --report <project_dir>/accessibility-report.md
  ```

  Without `--fix` it is read-only. With `--fix` it edits only `lang`/`dir` on `<html>` and
  positive `tabindex` values.
- Background on the law and the rule-to-WCAG mapping: `il-accessibility-audit/references/`.
- To install the skill for a user, follow `INSTALL.md`.
- `.claude-plugin/` makes the repo a Claude Code plugin marketplace; `plugin.json` points its
  `skills` at `./il-accessibility-audit`. Bump `version` in `plugin.json` on every release, or
  installed copies won't update. Check with `claude plugin validate .`.
- When changing `scan.py`, run it against a small sample project with known issues (an `<img>`
  without `alt`, an `<input>` without a label, a `tabindex="5"`, a low-contrast CSS rule) and
  confirm the JSON output lists each one. There is no test suite beyond that.
