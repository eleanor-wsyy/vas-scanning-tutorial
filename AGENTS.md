# Repository Guidelines

## Project Structure & Module Organization

`docs/` contains the English and Chinese tutorials, the PDF handout, sources, and references. `skills/vas-scanning/` is the installable Codex skill: its `SKILL.md` is the entry point, `references/` holds protocol and tool details, `scripts/` contains local preflight, report-import, rendering, and optional metric tools, and `assets/` contains documented numeral templates. `integrations/` explains compatibility with the separate Michael Diamant workflow. `tests/` contains synthetic fixtures and unit tests. The root `scripts/build_tutorial_pdf.py` rebuilds the handout.

## Setup, Build & Test

Use Python 3.10+ and install local-tool dependencies with `python -m pip install -r requirements.txt`. Run `python -m unittest discover -s tests -v` before committing; it tests preflight, archive safety, default image rendering, and opt-in metrics without contacting 3M. Run `python skills/vas-scanning/scripts/preflight.py image.jpg --output preflight.json` to inspect a local image. The CLI examples in `README.md` show report preparation and rendering. PDF rebuild dependencies are separate in `requirements-build.txt`; consult `scripts/build_tutorial_pdf.py` before changing the handout.

## Style & Conventions

Use four-space indentation for Python, descriptive `snake_case` names for modules and functions, and `test_*.py` for tests. Keep Markdown headings short and examples copyable. Preserve the distinction between native VAS outputs, edited composites, and researcher-defined calculations. Do not present R or C as default outputs; calculation requires an explicit user request. No formatter or linter is configured; run the tests and `git diff --check` instead.

## Testing & Review

Add synthetic, source-independent test cases for parser, layout, or metric changes. Verify that missing native evidence fails safely and that display-only changes cannot alter metrics. For visual changes, inspect the generated figure against the unchanged native report; tests alone do not validate genuine VAS results. Check the PDF visually after rebuilding it.

## Commits, PRs & Data Safety

Recent commits use short imperative subjects, such as `Prefer pedestrian viewpoints for architectural image selection`. Keep commits scoped. PRs should describe the protocol or behavior changed, list test results, and include before/after screenshots for output changes. Never commit source photographs, private chats, credentials, VAS report ZIPs, or unpublished scans. GitHub publication of a method or tool does not authorize publishing study data.
