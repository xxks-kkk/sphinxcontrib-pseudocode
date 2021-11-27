# -*- coding: utf-8 -*-
"""
    sphinx-algo
    ~~~~~~~~~~~

    Allow typeset algorithms in latex powered by pseudocode.js inside sphinx-doc

    :copyright: Copyright 2016-2021 by Zeyuan Hu, Martín Gaitán, and others, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import codecs
import os
import posixpath
import re
import shutil
from hashlib import sha1
from subprocess import Popen, PIPE
from tempfile import _get_default_tempdir
from tempfile import mkdtemp
from textwrap import dedent

import sphinx
from docutils import nodes
from docutils.parsers.rst import Directive, directives
from docutils.statemachine import ViewList
from sphinx.util import logging
from sphinx.util.i18n import search_image_for_language
from sphinx.util.osutil import ensuredir
import uuid

from .exceptions import MermaidError

logger = logging.getLogger(__name__)

mapname_re = re.compile(r'<map id="(.*?)"')

filename_autorenderer = 'katex_autorenderer.js'
MAXJAX_URL = 'https://cdn.jsdelivr.net/npm/mathjax@3.0.0/es5/tex-chtml.js'

class mermaid(nodes.General, nodes.Inline, nodes.Element):
    pass


def figure_wrapper(directive, node, caption):
    figure_node = nodes.figure('', node)
    if 'align' in node:
        figure_node['align'] = node.attributes.pop('align')

    parsed = nodes.Element()
    directive.state.nested_parse(ViewList([caption], source=''),
                                 directive.content_offset, parsed)
    caption_node = nodes.caption(parsed[0].rawsource, '',
                                 *parsed[0].children)
    caption_node.source = parsed[0].source
    caption_node.line = parsed[0].line
    figure_node += caption_node
    return figure_node


def align_spec(argument):
    return directives.choice(argument, ('left', 'center', 'right'))


class Mermaid(Directive):
    """
    Directive to insert arbitrary Mermaid markup.
    """
    has_content = True
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {}

    def get_mm_code(self):
        # inline mermaid code
        mmcode = '\n'.join(self.content)
        if not mmcode.strip():
            return [self.state_machine.reporter.warning(
                'Ignoring "mermaid" directive without content.',
                line=self.lineno)]
        return mmcode

    def run(self):

        node = mermaid()
        node['code'] = self.get_mm_code()
        node['options'] = {}
        if 'alt' in self.options:
            node['alt'] = self.options['alt']
        if 'align' in self.options:
            node['align'] = self.options['align']
        if 'inline' in self.options:
            node['inline'] = True

        caption = self.options.get('caption')
        if caption:
            node = figure_wrapper(self, node, caption)

        return [node]


def _render_mm_html_raw(self, node, code, options, prefix='mermaid',
                        imgcls=None, alt=None):
    tag_template = """<pre id="quicksort" style="display:hidden;">
            {code}
        </pre>"""

    self.body.append(tag_template.format(code=self.encode(code)))
    raise nodes.SkipNode


def render_mm_html(self, node, code, options, prefix='mermaid',
                   imgcls=None, alt=None):
    _fmt = self.builder.config.mermaid_output_format
    if _fmt == 'raw':
        return _render_mm_html_raw(self, node, code, options, prefix='mermaid',
                                   imgcls=None, alt=None)


def html_visit_mermaid(self, node):
    render_mm_html(self, node, node['code'], node['options'])

def write_katex_autorenderer_file(app, filename):
    filename = os.path.join(
        app.builder.srcdir, app._katex_static_path, filename
    )
    content = katex_autorenderer_content(app)
    with open(filename, 'w') as file:
        file.write(content)

def katex_autorenderer_content(app):
    content = dedent('''\
            document.addEventListener("DOMContentLoaded", function() {
              pseudocode.renderElement(document.getElementById("quicksort"));
            });
            ''')
    prefix = ''
    suffix = ''
    options = ''
    delimiters = ''
    return '\n'.join([prefix, options, delimiters, suffix, content])

def builder_inited(app):
    setup_static_path(app)
    install_js(app)

def install_js(app, *args):
    # add required javascript
    if app.config.mermaid_version == "latest":
        _mermaid_js_url = f"https://cdn.jsdelivr.net/npm/pseudocode@latest/build/pseudocode.js"
    if _mermaid_js_url:
        app.add_js_file(_mermaid_js_url)
    old_css_add = getattr(app, 'add_stylesheet', None)
    add_css = getattr(app, 'add_css_file', old_css_add)
    add_css(f"https://cdn.jsdelivr.net/npm/pseudocode@latest/build/pseudocode.min.css")
    # app.add_js_file(f"https://cdn.jsdelivr.net/npm/mathjax@3.0.0/es5/tex-chtml.js")
    # https://github.com/hagenw/sphinxcontrib-katex/blob/ce89a95b3b330a19ad4562b87aacc69ddb6742f2/sphinxcontrib/katex.py#L185
    # https://stackoverflow.com/questions/38860740/alternative-for-executing-script-at-end-of-document-body
    write_katex_autorenderer_file(app, filename_autorenderer)
    app.add_js_file(filename_autorenderer)
    # options = {"tex": {"inlineMath": "[['$','$'], ['\\(','\\)']]", "displayMath": "[['$$','$$'], ['\\[','\\]']]", "processEscapes": "true", "processEnvironments": "true"}}
    # app.add_js_file(MAXJAX_URL, **options)
    # app.add_js_file(None, body='''    MathJax = {
    #     tex: {
    #         inlineMath: [['$','$'], ['\\(','\\)']],
    #         displayMath: [['$$','$$'], ['\\[','\\]']],
    #         processEscapes: true,
    #         processEnvironments: true,
    #     }
    # }''')
    # app.add_js_file(MAXJAX_URL)
    app.add_js_file(f"https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.11.1/katex.min.js")

def setup_static_path(app):
    app._katex_static_path = mkdtemp()
    if app._katex_static_path not in app.config.html_static_path:
        app.config.html_static_path.append(app._katex_static_path)


def builder_finished(app, exception):
    # Delete temporary dir used for _static file
    shutil.rmtree(app._katex_static_path)

def setup(app):
    app.add_node(mermaid,
                 html=(html_visit_mermaid, None))
    app.add_directive('mermaid', Mermaid)
    app.add_config_value('mermaid_version', 'latest', 'html')
    app.add_config_value('mermaid_output_format', 'raw', 'html')
    app.connect('builder-inited', builder_inited)
    app.connect('build-finished', builder_finished)
    # app.connect('html-page-context', install_js)

    return {'version': sphinx.__display_version__, 'parallel_read_safe': True}
