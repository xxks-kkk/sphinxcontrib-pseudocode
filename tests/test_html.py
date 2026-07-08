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


# ---------------------------------------------------------------------------
# :ref: inside pcode blocks (test-ref testroot)
# ---------------------------------------------------------------------------

@pytest.mark.sphinx('html', testroot="ref")
def test_ref_undefined_label_emits_warning(app, warning):
    """An unresolvable :ref: inside a pcode block must emit a Sphinx warning.

    This mirrors the behaviour of a plain :ref: in prose for an unknown label.
    """
    app.build()
    assert 'no-such-label' in warning.getvalue(), (
        'Expected a warning mentioning the undefined label "no-such-label"'
    )

@pytest.fixture
def index_ref(app, build_all):
    return (app.outdir / 'index.html').read_text()


@pytest.fixture
def autorenderer_js_ref(app, build_all):
    return (app.outdir / '_static' / 'pseudocode_autorenderer_index.js').read_text()


@pytest.mark.sphinx('html', testroot="ref")
def test_ref_placeholder_in_pre(index_ref):
    """:ref: inside pcode must be replaced by a PCSREF placeholder in the <pre> element.

    The raw :ref:`...` markup must not reach pseudocode.js; it would be
    rendered as literal text.  Instead _resolve_refs_in_code() substitutes
    each :ref: with a unique PCSREF<N> token before the <pre> is emitted.
    """
    pre_blocks = re.findall(r'<pre[^>]*>(.*?)</pre>', index_ref, re.DOTALL)
    assert any('PCSREF' in block for block in pre_blocks), (
        'Expected a PCSREF placeholder inside a <pre> element'
    )
    assert not any(':ref:' in block for block in pre_blocks), (
        'Raw :ref: markup must not appear inside any <pre> element'
    )


@pytest.mark.sphinx('html', testroot="ref")
def test_ref_autorenderer_contains_replacement_data(autorenderer_js_ref):
    """The autorenderer JS must carry the placeholder→href mapping for :ref: links.

    After pseudocode.js renders the algorithm, a JS IIFE reads this data and
    swaps each PCSREF placeholder in the container's innerHTML for an <a> tag.
    """
    assert 'PCSREF0' in autorenderer_js_ref
    assert '"placeholder"' in autorenderer_js_ref
    assert '"href"' in autorenderer_js_ref
    assert 'Base Algorithm' in autorenderer_js_ref


@pytest.mark.sphinx('html', testroot="ref")
def test_ref_bare_form_uses_section_title(autorenderer_js_ref):
    """A bare :ref:`label` must render the section title, not the label.

    Sphinx's std domain stores the section title alongside each label; a
    :ref: without an explicit <target> uses that title as the link text.
    :ref: inside pcode blocks must behave the same way.
    """
    assert '"text": "Extending to Multiple Strings"' in autorenderer_js_ref, (
        'Bare :ref: link text must be the section title'
    )
    assert '"text": "sec-multiple-strings"' not in autorenderer_js_ref, (
        'Bare :ref: link text must not be the raw label'
    )


@pytest.mark.sphinx('html', testroot="ref")
def test_ref_autorenderer_captures_container_before_render(autorenderer_js_ref):
    """Within the ref-bearing IIFE, pcsContainer must be saved before renderElement().

    pseudocode.js calls elem.replaceWith(), which removes the <pre> from the
    DOM.  Any getElementById() call after that returns null.  The IIFE must
    therefore capture parentElement before the renderElement() call.
    """
    # Find where pcsContainer is assigned (only present in IIFEs that have refs).
    container_pos = autorenderer_js_ref.find('pcsContainer = pcsEl')
    assert container_pos != -1, 'pcsContainer assignment not found in autorenderer'

    # The renderElement call in the SAME IIFE must come after the assignment.
    # Searching forward from container_pos skips any renderElement calls in
    # earlier IIFEs (which have no refs) and lands on the one in this IIFE.
    render_pos = autorenderer_js_ref.find('pseudocode.renderElement', container_pos)
    assert render_pos != -1, (
        'No pseudocode.renderElement found after pcsContainer assignment'
    )
    assert container_pos < render_pos, (
        'pcsContainer must be captured before pseudocode.renderElement() is called'
    )


# ---------------------------------------------------------------------------
# :eq: inside pcode blocks (test-eq testroot)
# ---------------------------------------------------------------------------

@pytest.mark.sphinx('html', testroot="eq")
def test_eq_undefined_label_emits_warning(app, warning):
    """An unresolvable :eq: inside a pcode block must emit a Sphinx warning.

    This mirrors the behaviour of a plain :eq: in prose for an unknown label.
    """
    app.build()
    assert 'no-such-equation' in warning.getvalue(), (
        'Expected a warning mentioning the undefined equation "no-such-equation"'
    )


@pytest.fixture
def index_eq(app, build_all):
    return (app.outdir / 'index.html').read_text()


@pytest.fixture
def autorenderer_js_eq(app, build_all):
    return (app.outdir / '_static' / 'pseudocode_autorenderer_index.js').read_text()


@pytest.mark.sphinx('html', testroot="eq")
def test_eq_placeholder_in_pre(index_eq):
    """:eq: inside pcode must be replaced by a PCSREF placeholder in the <pre>.

    The raw :eq:`...` markup must not reach pseudocode.js; it would be
    rendered as literal text.  Instead it is substituted with a unique
    PCSREF<N> token before the <pre> is emitted, exactly like :ref:.
    """
    pre_blocks = re.findall(r'<pre[^>]*>(.*?)</pre>', index_eq, re.DOTALL)
    assert any('PCSREF' in block for block in pre_blocks), (
        'Expected a PCSREF placeholder inside a <pre> element'
    )
    assert not any(':eq:' in block for block in pre_blocks), (
        'Raw :eq: markup must not appear inside any <pre> element'
    )


@pytest.mark.sphinx('html', testroot="eq")
def test_eq_autorenderer_contains_equation_link(autorenderer_js_eq):
    """The autorenderer JS must carry the placeholder→href mapping for :eq: links.

    The href must point at the equation anchor and the link text must be the
    formatted equation number (default ``(1)``).
    """
    assert '"placeholder"' in autorenderer_js_eq
    assert '"href"' in autorenderer_js_eq
    assert 'equation-my-equation' in autorenderer_js_eq, (
        'Expected href to the equation anchor "#equation-my-equation"'
    )
    assert '(1)' in autorenderer_js_eq, (
        'Expected the formatted equation number "(1)" as the link text'
    )



# ---------------------------------------------------------------------------
# pcode blocks without a figure number (test-nonumfig testroot)
# ---------------------------------------------------------------------------

@pytest.mark.sphinx('html', testroot="nonumfig")
def test_pcode_without_fignumber_emits_warning(app, warning):
    """A pcode block with no figure number must emit a Sphinx warning.

    Without numfig = True (or for a document outside every toctree) Sphinx
    assigns no figure number, the <pre> gets an empty id, and the
    autorenderer silently skips the block.  A warning must explain why the
    block will not render and how to fix it.
    """
    app.build()
    assert 'numfig' in warning.getvalue(), (
        'Expected a warning telling the user to set numfig = True'
    )
    assert "suppress_warnings = ['pseudocode.nonumber']" in warning.getvalue(), (
        'Expected the warning to spell out how to silence it'
    )
