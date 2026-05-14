"""Tests for sphinxcontrib-pseudocode HTML output.

Test scope
----------
These are *static* tests: they build HTML with Sphinx and inspect the generated
files.  They cannot execute JavaScript, so they cannot verify that pseudocode.js
actually renders an algorithm in a browser.  What they CAN verify:

* The correct Sphinx/Python-side HTML is emitted (pre elements, hidden-div
  macros, caption numbers, …).
* The autorenderer JS is well-formed and wires up every numbered block.
* Required runtime configuration is present (MathJax version, macro
  pre-configuration, MathJax 4 polyfill).

For true rendering validation (does pseudocode.js produce the expected SVG/HTML
in a real browser?) browser-level tests using Playwright or Selenium would be
needed.  CI failures from the tests below indicate *setup* problems that would
prevent rendering; a green run does not guarantee rendering is pixel-perfect.
"""

import io
import re
from pathlib import Path

import pytest
from sphinx.application import Sphinx

DOCS_DIR = Path(__file__).parent.parent / 'docs'


# ---------------------------------------------------------------------------
# Shared fixtures for test-root builds
# ---------------------------------------------------------------------------

@pytest.fixture
def build_all(app):
    app.builder.build_all()


@pytest.fixture
def index(app, build_all):
    # normalize script tag for compat to Sphinx<4
    return (app.outdir / 'index.html').read_text().replace("<script >", "<script>")


# ---------------------------------------------------------------------------
# Basic rendering tests
# ---------------------------------------------------------------------------

@pytest.mark.sphinx('html', testroot="basic")
def test_html_raw(index):
    assert 'cdn.jsdelivr.net/npm/pseudocode@latest/build/pseudocode.js' in index
    assert 'katex' not in index.lower()
    assert '<span class="caption-number">Fig. 1 </span>' in index


@pytest.mark.sphinx('html', testroot="basic")
def test_autorenderer_js_written_to_static(app, build_all):
    """pseudocode_autorenderer_<page>.js must exist in _static/ after build.

    Regression test: Sphinx 8+ copies assets before writing pages, so the
    file must be written directly to outdir/_static/ rather than a temp dir
    that gets copied during the asset phase (which runs before html-page-context).
    """
    js_file = app.outdir / '_static' / 'pseudocode_autorenderer_index.js'
    assert js_file.exists(), (
        f"{js_file} not found — autorenderer JS was not written to _static/"
    )
    assert 'DOMContentLoaded' in js_file.read_text()


# ---------------------------------------------------------------------------
# \\newcommand / macro tests (test-newcommand testroot)
# ---------------------------------------------------------------------------

@pytest.fixture
def index_newcommand(app, build_all):
    return (app.outdir / 'index.html').read_text()


@pytest.fixture
def autorenderer_js_newcommand(app, build_all):
    return (app.outdir / '_static' / 'pseudocode_autorenderer_index.js').read_text()


@pytest.mark.sphinx('html', testroot="newcommand")
def test_html_newcommand(index_newcommand):
    assert r'\newcommand{\floor}[1]{\lfloor #1 \rfloor}' in index_newcommand
    assert r'\newcommand{\ceil}[1]{\lceil #1 \rceil}' in index_newcommand


@pytest.mark.sphinx('html', testroot="newcommand")
def test_inline_newcommand_stripped(index_newcommand):
    """Inline \\newcommand must not appear inside the <pre> pseudocode block."""
    pre_match = re.search(r'<pre[^>]*>(.*?)</pre>', index_newcommand, re.DOTALL)
    assert pre_match is not None
    assert r'\newcommand' not in pre_match.group(1)


@pytest.mark.sphinx('html', testroot="newcommand")
def test_page_macros_extracted(index_newcommand):
    """Per-page \\newcommand from math blocks must appear in the HTML."""
    assert r'\newcommand{\ceil}[1]{\lceil #1 \rceil}' in index_newcommand


@pytest.mark.sphinx('html', testroot="newcommand")
def test_macros_pre_configured_in_window_mathjax(autorenderer_js_newcommand):
    """Macros must be injected into window.MathJax.tex.macros before MathJax loads.

    The autorenderer runs synchronously during HTML parsing while MathJax is
    deferred, so writing to window.MathJax.tex.macros here guarantees the macros
    are built into MathJax from startup — more reliable than calling tex2chtml()
    after the fact.
    """
    assert 'window.MathJax.tex.macros' in autorenderer_js_newcommand
    # Macro names appear as JSON object keys (without backslash).
    assert '"floor"' in autorenderer_js_newcommand
    assert '"ceil"' in autorenderer_js_newcommand



# ---------------------------------------------------------------------------
# Docs integration tests — build docs/ and verify static setup is correct.
#
# IMPORTANT: These tests check HTML/JS *structure*, not browser rendering.
# A passing run means the Sphinx-side setup is correct; it does NOT guarantee
# that pseudocode.js will render blocks correctly in a browser.
#
# The single hard CI gate for actual renderability is test_docs_mathjax3_pinned:
# if that test fails, blocks WILL fail to render at runtime.
# ---------------------------------------------------------------------------

@pytest.fixture(scope='module')
def built_docs(tmp_path_factory):
    """Build the actual docs/ directory once per test module."""
    outdir = tmp_path_factory.mktemp('docs_build')
    app = Sphinx(
        srcdir=str(DOCS_DIR),
        confdir=str(DOCS_DIR),
        outdir=str(outdir),
        doctreedir=str(outdir / '.doctrees'),
        buildername='html',
        warning=io.StringIO(),
    )
    app.build()
    return outdir


@pytest.fixture(scope='module')
def docs_index_html(built_docs):
    return (built_docs / 'index.html').read_text()


@pytest.fixture(scope='module')
def docs_autorenderer_js(built_docs):
    return (built_docs / '_static' / 'pseudocode_autorenderer_index.js').read_text()


def test_docs_all_numbered_blocks_wired_to_autorenderer(docs_index_html, docs_autorenderer_js):
    """Every numbered pcode block must have a matching renderElement call.

    Structural check only: verifies every <pre id="N"> in the HTML has a
    corresponding renderElement("N") call in the autorenderer JS.  This catches
    blocks that were silently dropped from the autorenderer (left permanently
    hidden as raw <pre> elements regardless of JS engine).

    Does NOT verify that pseudocode.js successfully renders each block —
    that requires browser testing.
    """
    pre_ids = {m for m in re.findall(r'<pre id="([^"]*)"', docs_index_html) if m}
    assert pre_ids, "No numbered pcode blocks found in docs output"
    for pre_id in sorted(pre_ids):
        assert f'getElementById("{pre_id}")' in docs_autorenderer_js, (
            f'pcode block id="{pre_id}" has no renderElement call in the autorenderer'
        )


def test_docs_mathjax3_pinned(docs_index_html):
    """docs/conf.py MUST pin MathJax 3 — this is a hard rendering requirement.

    pseudocode.js v2.4.1 (@latest) calls MathJax.tex2chtml() for every math
    expression.  MathJax 4 removed that function, so all blocks with math will
    silently fail to render when MathJax 4 is loaded.  MathJax 4 support is
    merged upstream but not yet released; remove this pin once a new pseudocode.js
    version with MathJax 4 support is published to npm.

    This test is the authoritative CI gate: if it fails, math blocks WILL NOT
    render in a browser regardless of any other setup.  Restore mathjax_path
    in docs/conf.py to fix it.
    """
    assert 'mathjax@3' in docs_index_html, (
        "docs/conf.py must set mathjax_path to mathjax@3. "
        "MathJax 4 removed tex2chtml, breaking pseudocode.js math rendering."
    )


def test_docs_page_macros_pre_configured(docs_autorenderer_js):
    """Per-page macros from demo.rst must appear in window.MathJax.tex.macros."""
    assert 'window.MathJax.tex.macros' in docs_autorenderer_js
    assert '"ceil"' in docs_autorenderer_js    # from .. math:: block in demo.rst
    assert '"floor"' in docs_autorenderer_js   # from inline \\newcommand in demo.rst


