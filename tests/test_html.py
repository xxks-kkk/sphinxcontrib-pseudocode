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
    assert '<script src="https://cdn.jsdelivr.net/npm/pseudocode@latest/build/pseudocode.js"></script>' in index
    assert '<script src="https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.11.1/katex.min.js"></script>' in index
    assert '<script src="_static/katex_autorenderer.js"></script>' in index
