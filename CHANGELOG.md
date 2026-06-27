# Changelog

## Unreleased

### New Features

- **Cross-references inside `pcode` blocks.** You can now use Sphinx
  cross-reference roles inside an algorithm body; they are resolved at build
  time and rendered as clickable links:
  - **`:ref:`** links to any labeled element (e.g. another algorithm). Supports
    both `:ref:`label`` and `:ref:`display text <label>``.
  - **`:eq:`** links to a labeled `.. math::` equation, rendered as the
    equation number (e.g. `(2)`), matching `:eq:` behavior in prose.

## v0.8.0

### New Features

- **`\newcommand` macro support in pcode blocks.** LaTeX macros can now be defined in three places and will render correctly inside algorithm blocks:
  - **Global**: via `mathjax3_config` in `conf.py`
  - **Per-page**: defined in `.. math::` blocks anywhere on the page
  - **Inline**: defined directly inside a `pcode` block (stripped before passing to pseudocode.js)

### Bug Fixes

- **Sphinx 8+ compatibility**: Fixed autorenderer JS files not being copied to `_static/` on Sphinx 8+. This caused pseudocode blocks to silently fail to render in the browser.
- **`\newcommand` rendering**: Fixed per-page `\newcommand` macros not being available when pseudocode.js renders math inside algorithm blocks.
- Fixed figure numbering being overridden when `numfig = True` is set in `conf.py`.
- Fixed numbering inconsistency in algorithm captions.
- Fixed some characters not rendering visibly.

### Important: MathJax 3 Required

This release switches from KaTeX to **MathJax 3**. This is a deliberate choice driven by macro support: KaTeX only supports `\newcommand` for macros defined upfront in its config and cannot process them dynamically within content, which makes per-page and inline macro definitions structurally impossible. MathJax 3 handles `\newcommand` as a first-class part of its rendering pipeline, supporting inline, per-page, and global definitions correctly.

Add the following to your `conf.py`:

```python
mathjax_path = "https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"
```

### Infrastructure

- Migrated from `setup.py`/`setup.cfg` to `pyproject.toml` with `uv`
- Automated PyPI publishing via GitHub Actions (Trusted Publishing)
- Updated CI to Python 3.10–3.12
