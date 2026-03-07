# Design: LaTeX \newcommand Support in pcode

**Date:** 2026-03-07

## Goal

Allow custom LaTeX macros (defined via `\newcommand`) to be used inside `pcode` blocks, supporting three declaration sources: global (`conf.py`), per-page (`.. math::` blocks), and inline (inside the `pcode` block itself).

## Switch from KaTeX to MathJax3

pseudocode.js auto-detects MathJax3 when present. Since users already have `sphinx.ext.mathjax` loaded, we switch to MathJax3 by removing KaTeX from the extension's JS loading. This makes global macros work for free.

## Macro Sources

### 1. Global macros (free — no extension changes)

The user's existing `mathjax3_config["tex"]["macros"]` in `conf.py` is automatically picked up by pseudocode.js via MathJax3. No new config value needed.

### 2. Per-page macros from `.. math::` blocks

During the `html-page-context` event (`install_js2_part2`), traverse `nodes.math_block` in the doctree and extract `\newcommand` declarations using regex:

```python
re.findall(r'\\newcommand\{(\\[^}]+)\}\{([^}]+)\}', math_content)
```

Emit a hidden `<div style="display:none">` containing all extracted declarations as display math (`\[...\]`) before each pcode block in the HTML. MathJax3 processes this element and registers the macros globally.

### 3. Inline `\newcommand` in pcode content

Strip leading `\newcommand` lines from the pcode content before passing it to pseudocode.js (so pseudocode.js does not try to parse them as pseudocode). Collect the stripped declarations and inject them via the same hidden `<div>` approach.

## Implementation Touchpoints

| Component | Change |
|---|---|
| `install_js()` | Remove KaTeX CDN JS + CSS loading |
| `PROOF_HTML_TITLE_TEMPLATE_VISIT` | Remove `macros` option from `renderElement()` |
| `render_mm_html()` | Emit hidden `<div>` with extracted macros before `<pre>` |
| `Pseudocode.run()` | Strip leading `\newcommand` lines from content; store them on node |
| `install_js2_part2()` | Extract `\newcommand` from `nodes.math_block` in doctree; attach to pcode nodes |

## Decisions

- Only `\newcommand` (no-arg and with-arg) is extracted from math blocks — `\DeclareMathOperator`, `\DeclarePairedDelimiter` etc. are ignored (not reliably mappable to KaTeX/MathJax macros inline)
- Extracted per-page macros apply to all pcode blocks on the same page
- Inline macros (stripped from pcode content) apply only to that pcode block
- Global macros require no extension support — entirely handled by user's `mathjax3_config`
