# \newcommand Support in pcode Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Allow LaTeX `\newcommand` macros to be used inside `pcode` blocks via three sources: global (`mathjax3_config` in conf.py — free), per-page (`.. math::` blocks), and inline (inside the `pcode` block itself).

**Architecture:** Switch pseudocode.js from KaTeX to MathJax3 (auto-detected when `sphinx.ext.mathjax` is loaded). A `doctree-resolved` handler extracts `\newcommand` declarations from math blocks and stores them on each `pseudocodeContentNode`. The `Pseudocode` directive strips leading `\newcommand` lines from pcode content and stores them on the node. At HTML render time, a hidden `<div>` containing all macros as display math is emitted before each `<pre>` tag so MathJax3 registers them before rendering pseudocode.

**Tech Stack:** Python, docutils node traversal, Sphinx events (`doctree-resolved`, `html-page-context`), MathJax3, pseudocode.js

---

### Task 1: Remove KaTeX, switch to MathJax3

pseudocode.js auto-detects MathJax3 when it is already on the page. The only change needed is to stop loading KaTeX.

**Files:**
- Modify: `sphinxcontrib/pseudocode.py:136-143` (`install_js`)
- Modify: `tests/test_html.py`

**Step 1: Write the failing test**

In `tests/test_html.py`, update `test_html_raw` to assert KaTeX is NOT loaded:

```python
@pytest.mark.sphinx('html', testroot="basic")
def test_html_raw(index):
    assert '<script src="https://cdn.jsdelivr.net/npm/pseudocode@latest/build/pseudocode.js"></script>' in index
    assert 'katex' not in index.lower()
    assert '<span class="caption-number">Fig. 1 </span>' in index
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_html.py::test_html_raw -v
```

Expected: FAIL — `katex` is still present in the output.

**Step 3: Remove KaTeX from `install_js`**

Replace the `install_js` function in `sphinxcontrib/pseudocode.py`:

```python
def install_js(app, *args):
    app.add_js_file("https://cdn.jsdelivr.net/npm/pseudocode@latest/build/pseudocode.js")
    old_css_add = getattr(app, 'add_stylesheet', None)
    add_css = getattr(app, 'add_css_file', old_css_add)
    add_css("https://cdn.jsdelivr.net/npm/pseudocode@latest/build/pseudocode.min.css")
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/test_html.py::test_html_raw -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add sphinxcontrib/pseudocode.py tests/test_html.py
git commit -m "feat: switch from KaTeX to MathJax3 for pseudocode.js rendering"
```

---

### Task 2: Strip inline `\newcommand` from pcode content

When a user writes `\newcommand` lines at the top of a `pcode` block, strip them from the code (so pseudocode.js does not try to parse them as pseudocode) and store them on the node.

**Files:**
- Modify: `sphinxcontrib/pseudocode.py`
- Create: `tests/roots/test-newcommand/conf.py`
- Create: `tests/roots/test-newcommand/index.rst`
- Modify: `tests/test_html.py`

**Step 1: Create the test root**

Create `tests/roots/test-newcommand/conf.py`:

```python
extensions = ['sphinxcontrib.pseudocode']
exclude_patterns = ['_build']
```

Create `tests/roots/test-newcommand/index.rst`:

```rst
Newcommand test
---------------

.. math::

   \newcommand{\bigo}{\mathcal{O}}

.. pcode::

   \newcommand{\ah}{\mathsf{ah}}
   \begin{algorithmic}
   \STATE Use $\ah$ and $\bigo(n)$
   \end{algorithmic}
```

**Step 2: Write the failing test**

Add to `tests/test_html.py`:

```python
@pytest.fixture
def index_newcommand(app, build_all):
    return (app.outdir / 'index.html').read_text()


@pytest.mark.sphinx('html', testroot="newcommand")
def test_inline_newcommand_stripped(index_newcommand):
    # \newcommand must not appear inside the <pre> pseudocode block
    import re
    pre_match = re.search(r'<pre[^>]*>(.*?)</pre>', index_newcommand, re.DOTALL)
    assert pre_match is not None
    assert r'\newcommand' not in pre_match.group(1)
```

**Step 3: Run test to verify it fails**

```bash
uv run pytest tests/test_html.py::test_inline_newcommand_stripped -v
```

Expected: FAIL — `\newcommand` is still present inside `<pre>`.

**Step 4: Add regex import and helper to strip `\newcommand` lines**

In `sphinxcontrib/pseudocode.py`, update `get_mm_code` in the `Pseudocode` class and add a module-level helper:

```python
_NEWCOMMAND_RE = re.compile(
    r'\\newcommand\{(\\[^}]+)\}(?:\[(\d+)\])?\{((?:[^{}]|\{[^{}]*\})*)\}'
)


def _extract_newcommands(text):
    """Return (stripped_text, list_of_raw_newcommand_strings)."""
    lines = text.split('\n')
    newcommands = []
    code_lines = []
    in_preamble = True
    for line in lines:
        stripped = line.strip()
        if in_preamble and stripped.startswith(r'\newcommand'):
            newcommands.append(stripped)
        else:
            in_preamble = False
            code_lines.append(line)
    return '\n'.join(code_lines), newcommands
```

Update `get_mm_code` and `run` in the `Pseudocode` class:

```python
def get_mm_code(self):
    pcode = '\n'.join(self.content)
    if not pcode.strip():
        return [self.state_machine.reporter.warning(
            'Ignoring "pcode" directive without content.',
            line=self.lineno)]
    return pcode

def run(self):
    node = pseudocode()
    raw_code = self.get_mm_code()
    stripped_code, inline_macros = _extract_newcommands(raw_code)
    node['code'] = stripped_code
    node = pseudocode_wrapper(self, node)

    content = pseudocodeContentNode()
    content['code'] = stripped_code
    content['options'] = {}
    content['inline_macros'] = inline_macros
    content['page_macros'] = []  # filled in by doctree-resolved handler
    if 'linenos' in self.options:
        content['linenos'] = True

    node += content
    self.add_name(node)
    return [node]
```

**Step 5: Run test to verify it passes**

```bash
uv run pytest tests/test_html.py::test_inline_newcommand_stripped -v
```

Expected: PASS

**Step 6: Commit**

```bash
git add sphinxcontrib/pseudocode.py tests/roots/test-newcommand/ tests/test_html.py
git commit -m "feat: strip inline \\newcommand lines from pcode content"
```

---

### Task 3: Extract `\newcommand` from `.. math::` blocks via `doctree-resolved`

Connect a `doctree-resolved` event handler that scans the doctree for math blocks, extracts `\newcommand` declarations, and stores them on every `pseudocodeContentNode` in the same document.

**Files:**
- Modify: `sphinxcontrib/pseudocode.py`
- Modify: `tests/test_html.py`

**Step 1: Write the failing test**

Add to `tests/test_html.py`:

```python
@pytest.mark.sphinx('html', testroot="newcommand")
def test_page_macros_extracted(app, build_all):
    # Verify that the doctree-resolved handler stores page_macros on the node.
    # We check this indirectly: the hidden macro div must appear in the HTML.
    index = (app.outdir / 'index.html').read_text()
    assert r'\newcommand{\bigo}' in index
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_html.py::test_page_macros_extracted -v
```

Expected: FAIL — `\newcommand{\bigo}` is not yet injected into the HTML.

**Step 3: Add `doctree-resolved` handler**

Add this function to `sphinxcontrib/pseudocode.py`:

```python
def doctree_resolved(app, doctree, docname):
    """Extract \\newcommand from math blocks and attach to pcode nodes."""
    page_macros = []
    for math_node in doctree.findall(nodes.math_block):
        content = math_node.astext()
        for raw in _NEWCOMMAND_RE.findall(content):
            # raw is (cmd, nargs, body) tuple from findall
            cmd, nargs, body = raw
            if nargs:
                page_macros.append(f'\\newcommand{{{cmd}}}[{nargs}]{{{body}}}')
            else:
                page_macros.append(f'\\newcommand{{{cmd}}}{{{body}}}')

    for content_node in doctree.findall(pseudocodeContentNode):
        content_node['page_macros'] = list(page_macros)
```

Register it in `setup`:

```python
app.connect('doctree-resolved', doctree_resolved)
```

**Step 4: Run test to verify it fails (still — hidden div not emitted yet)**

```bash
uv run pytest tests/test_html.py::test_page_macros_extracted -v
```

Expected: FAIL — macros are extracted but not yet emitted into HTML. (This confirms the handler runs without error.)

**Step 5: Commit**

```bash
git add sphinxcontrib/pseudocode.py
git commit -m "feat: extract \\newcommand from math blocks via doctree-resolved"
```

---

### Task 4: Emit hidden macro `<div>` before each `<pre>` tag

Combine per-page and inline macros from the node and emit a hidden `<div>` containing display math so MathJax3 registers them before rendering the pseudocode.

**Files:**
- Modify: `sphinxcontrib/pseudocode.py` (`render_mm_html`)
- Modify: `tests/test_html.py`

**Step 1: Write the failing test** (already written in Task 3 Step 1 — reuse it)

The test `test_page_macros_extracted` already checks for `\newcommand{\bigo}` in the HTML. Run it:

```bash
uv run pytest tests/test_html.py::test_page_macros_extracted -v
```

Expected: FAIL (confirms hidden div is not yet emitted).

**Step 2: Update `render_mm_html` to emit the hidden macro div**

Replace `render_mm_html` in `sphinxcontrib/pseudocode.py`:

```python
def render_mm_html(self, node, code, options, prefix='pseudocode',
                   imgcls=None, alt=None):
    # Collect all macros: page-level first, then inline (inline wins on conflict)
    all_macros = node.get('page_macros', []) + node.get('inline_macros', [])
    if all_macros:
        macro_math = ''.join(all_macros)
        self.body.append(
            f'<div style="display:none">\\[{macro_math}\\]</div>'
        )

    tag_template = """<pre id="{id}" style="display:hidden;">
            {code}
        </pre>"""
    self.body.append(tag_template.format(id=get_fignumber(self, node), code=self.encode(code)))
    node['id'] = get_fignumber(self, node)
```

**Step 3: Run all tests**

```bash
uv run pytest tests/ -v
```

Expected: all tests pass, including:
- `test_html_raw` — pseudocode.js loaded, KaTeX absent
- `test_inline_newcommand_stripped` — `\newcommand` absent from `<pre>`
- `test_page_macros_extracted` — `\newcommand{\bigo}` present in HTML

**Step 4: Commit**

```bash
git add sphinxcontrib/pseudocode.py tests/test_html.py
git commit -m "feat: emit hidden macro div before pcode pre tag for MathJax3 registration"
```

---

### Task 5: Final verification

**Step 1: Run full test suite**

```bash
uv run pytest -v
```

Expected: all tests pass, no failures.

**Step 2: Build the docs to check for regressions**

```bash
cd docs && uv run make html 2>&1 | tail -20
```

Expected: no errors (warnings about missing extensions are OK if mathjax is not configured in the docs conf).

**Step 3: Commit if any fixups were needed, then verify git log**

```bash
git log --oneline -8
```
