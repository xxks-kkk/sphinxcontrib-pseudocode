import re

import pytest


@pytest.fixture
def build_all(app):
    app.builder.build_all()


@pytest.fixture
def index(app, build_all):
    # normalize script tag for compat to Sphinx<4
    return (app.outdir / 'index.html').read_text().replace("<script >", "<script>")


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


@pytest.fixture
def index_newcommand(app, build_all):
    return (app.outdir / 'index.html').read_text()


@pytest.mark.sphinx('html', testroot="newcommand")
def test_html_newcommand(index_newcommand):
    assert r'\newcommand{\floor}[1]{\lfloor #1 \rfloor}' in index_newcommand
    assert r'\newcommand{\ceil}[1]{\lceil #1 \rceil}' in index_newcommand


@pytest.mark.sphinx('html', testroot="newcommand")
def test_inline_newcommand_expanded_in_pre(index_newcommand):
    """\\newcommand definitions must be expanded in the <pre> block sent to
    pseudocode.js, and the raw \\newcommand lines must be absent (pseudocode.js
    does not support \\newcommand and will throw a ParseError if it sees one)."""
    pre_match = re.search(r'<pre[^>]*>(.*?)</pre>', index_newcommand, re.DOTALL)
    assert pre_match is not None
    pre_content = pre_match.group(1)
    assert r'\newcommand' not in pre_content
    # \floor{3.14} should have been expanded to \lfloor 3.14 \rfloor
    assert r'\lfloor 3.14 \rfloor' in pre_content


@pytest.mark.sphinx('html', testroot="newcommand")
def test_page_macros_extracted(index_newcommand):
    """Per-page \\newcommand from math blocks must appear in the HTML."""
    assert r'\newcommand{\ceil}[1]{\lceil #1 \rceil}' in index_newcommand
