# -*- coding: utf-8 -*-
"""
    sphinx-pseudocode
    ~~~~~~~~~~~~~~~~~

    Allow typeset algorithms in latex powered by pseudocode.js inside sphinx-doc

    :copyright: Copyright 2016-2021 by Zeyuan Hu, Martín Gaitán, and others, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os
import re
import shutil
import uuid
from tempfile import mkdtemp
from textwrap import dedent

import sphinx
from docutils import nodes
from docutils.parsers.rst import Directive, directives
from docutils.statemachine import ViewList
from sphinx.util import logging

logger = logging.getLogger(__name__)

mapname_re = re.compile(r'<map id="(.*?)"')

filename_autorenderer = 'katex_autorenderer.js'


class pseudocode(nodes.General, nodes.Inline, nodes.Element):
    pass


def align_spec(argument):
    return directives.choice(argument, ('left', 'center', 'right'))


class Pseudocode(Directive):
    has_content = True
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {
        'linenos': directives.unchanged
    }

    def get_mm_code(self):
        # inline pseudocode code
        pcode = '\n'.join(self.content)
        if not pcode.strip():
            return [self.state_machine.reporter.warning(
                'Ignoring "pcode" directive without content.',
                line=self.lineno)]
        return pcode

    def run(self):

        node = pseudocode()
        node['code'] = self.get_mm_code()
        node['id'] = uuid.uuid4()
        node['options'] = {}
        if 'linenos' in self.options:
            node['linenos'] = True

        return [node]


def _render_mm_html_raw(self, node, code, options, prefix='pseudocode',
                        imgcls=None, alt=None):
    tag_template = """<pre id="{id}" style="display:hidden;">
            {code}
        </pre>"""

    self.body.append(tag_template.format(id=node.get('id'), code=self.encode(code)))
    raise nodes.SkipNode


def render_mm_html(self, node, code, options, prefix='pseudocode',
                   imgcls=None, alt=None):
    _fmt = self.builder.config.pseudocode_output_format
    if _fmt == 'raw':
        return _render_mm_html_raw(self, node, code, options, prefix='pseudocode',
                                   imgcls=None, alt=None)


def html_visit_pseudocode(self, node):
    render_mm_html(self, node, node['code'], node['options'])


def write_katex_autorenderer_file(app, filename, dicts):
    filename = os.path.join(
        app.builder.srcdir, app._katex_static_path, filename
    )
    content = katex_autorenderer_content(app, dicts)
    with open(filename, 'w') as file:
        file.write(content)


def katex_autorenderer_content(app, dicts):
    content = dedent('''\
            document.addEventListener("DOMContentLoaded", function() {{
              {functions}
            }});''')
    functions = ''
    for pairs in dicts:
        functions += '''pseudocode.renderElement(document.getElementById("{id}"));\n'''.format(id=pairs['id']) if \
            pairs['linenos'] == False \
            else '''pseudocode.renderElement(document.getElementById("{id}"), {{lineNumber: true}});\n'''.format(
            id=pairs['id'])
    content = content.format(functions=functions)
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
    if app.config.pseudocode_version == "latest":
        _pseudocode_js_url = f"https://cdn.jsdelivr.net/npm/pseudocode@latest/build/pseudocode.js"
    if _pseudocode_js_url:
        app.add_js_file(_pseudocode_js_url)
    old_css_add = getattr(app, 'add_stylesheet', None)
    add_css = getattr(app, 'add_css_file', old_css_add)
    add_css(f"https://cdn.jsdelivr.net/npm/pseudocode@latest/build/pseudocode.min.css")
    app.add_js_file(f"https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.11.1/katex.min.js")


def install_js2(app, doctree, fromdocname):
    """
    Generate katex_autorenderer.js based on ids of each pcode and associated options so that
    we can create associate document.getElementById functions
    """
    dicts = []
    for node in doctree.traverse(pseudocode):
        pairs = {'id': node['id'], 'linenos': True if 'linenos' in node else False}
        dicts.append(pairs)
    write_katex_autorenderer_file(app, filename_autorenderer, dicts)


def install_js2_part2(app, pagename, templatename, context, doctree):
    """
    Register katex_autorenderer.js
    """
    app.add_js_file(filename_autorenderer)


def setup_static_path(app):
    app._katex_static_path = mkdtemp()
    if app._katex_static_path not in app.config.html_static_path:
        app.config.html_static_path.append(app._katex_static_path)


def builder_finished(app, exception):
    # Delete temporary dir used for _static file
    shutil.rmtree(app._katex_static_path)


def setup(app):
    app.add_node(pseudocode,
                 html=(html_visit_pseudocode, None))
    app.add_directive('pcode', Pseudocode)
    app.add_config_value('pseudocode_version', 'latest', 'html')
    app.add_config_value('pseudocode_output_format', 'raw', 'html')
    app.connect('builder-inited', builder_inited)
    app.connect('doctree-resolved', install_js2)
    app.connect('html-page-context', install_js2_part2)
    app.connect('build-finished', builder_finished)

    return {'version': sphinx.__display_version__, 'parallel_read_safe': True}
