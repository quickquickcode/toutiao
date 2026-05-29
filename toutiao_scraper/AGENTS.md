# Repository Guidelines

## Project Structure & Module Organization
This repository is a static snapshot of the Toutiao web client rather than a source-first application. The main entry point is `web/今日头条.html`. Supporting assets live in `web/今日头条_files/`, including bundled JavaScript (`*.js`), stylesheets (`*.css`), images (`*.jpg`, `*.jpeg`, `*.svg`), and other saved browser artifacts.

Keep edits narrowly scoped. Prefer changing the top-level HTML for markup adjustments and only touch bundled assets when a direct patch is necessary. Do not rename snapshot files unless you also update all references in `web/今日头条.html`.

## Build, Test, and Development Commands
There is no build system or package manifest in this directory. Use lightweight local checks instead:

- `open web/今日头条.html`: open the saved page in a browser on macOS.
- `python3 -m http.server 8000`: serve the repository locally if browser restrictions affect asset loading.
- `file web/今日头条.html`: verify file type and encoding before large edits.
- `rg "pattern" web`: locate HTML, CSS, or JS references quickly.

## Coding Style & Naming Conventions
Preserve the repository’s current snapshot layout and UTF-8 filenames. Use 2 spaces for any new HTML indentation and keep attribute or selector naming consistent with existing saved content. When adding helper files, prefer lowercase, descriptive names such as `notes.md` or `scripts/validate_snapshot.sh`.

Minimize formatting churn in bundled files. Small surgical edits are preferred over reformatting minified assets.

## Testing Guidelines
No automated test suite is present. Validate changes by loading `web/今日头条.html` in a browser and confirming that linked assets still resolve from `web/今日头条_files/`. For content or selector changes, re-run `rg` searches to confirm references stay in sync.

If you add scripts or utilities, include a simple invocation example in the file header or this document.

## Commit & Pull Request Guidelines
Git history is not available in this directory, so use clear, imperative commit messages such as `fix: update saved page asset references` or `docs: add repository contributor guide`.

Pull requests should include:

- a short summary of what changed and why
- the exact files touched
- manual verification steps performed
- screenshots only when the rendered page changed visibly

## Security & Snapshot Handling
Treat this repository as archived third-party content. Avoid introducing secrets, tokens, or live credentials. When updating external links or scripts, document the reason and confirm the snapshot still works offline where possible.
