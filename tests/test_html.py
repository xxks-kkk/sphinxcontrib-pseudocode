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


@pytest.fixture
def index_newcommand(app, build_all):
    return (app.outdir / 'index.html').read_text()


@pytest.mark.sphinx('html', testroot="newcommand")
def test_html_newcommand(index_newcommand):
    assert r'\newcommand{\floor}[1]{\lfloor #1 \rfloor}' in index_newcommand
    assert r'\newcommand{\ceil}[1]{\lceil #1 \rceil}' in index_newcommand


@pytest.mark.sphinx('html', testroot="newcommand")
def test_inline_newcommand_in_pre(index_newcommand):
    """Inline \\newcommand must appear inside the <pre> pseudocode block so
    pseudocode.js can use it for custom keyword definitions."""
    pre_match = re.search(r'<pre[^>]*>(.*?)</pre>', index_newcommand, re.DOTALL)
    assert pre_match is not None
    assert r'\newcommand' in pre_match.group(1)


@pytest.mark.sphinx('html', testroot="newcommand")
def test_page_macros_extracted(index_newcommand):
    """Per-page \\newcommand from math blocks must appear in the HTML."""
    assert r'\newcommand{\ceil}[1]{\lceil #1 \rceil}' in index_newcommand
