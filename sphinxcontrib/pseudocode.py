# -*- coding: utf-8 -*-
"""
    sphinx-pseudocode
    ~~~~~~~~~~~~~~~~~

    Allow typeset algorithms in latex powered by pseudocode.js inside sphinx-doc

    :copyright: Copyright 2021 by Zeyuan Hu.
    :license: BSD, see LICENSE for details.
"""

import os
import re
import shutil
from tempfile import mkdtemp
from textwrap import dedent

import jinja2
import sphinx
from docutils import nodes
from docutils.parsers.rst import Directive, directives
from docutils.statemachine import ViewList
from sphinx.domains.std import StandardDomain
from sphinx.util import logging
from sphinx.util.i18n import search_image_for_language
from sphinx.util.docutils import SphinxDirective
from sphinx.locale import __

logger = logging.getLogger(__name__)

mapname_re = re.compile(r'<map id="(.*?)"')

filename_autorenderer = 'katex_autorenderer_{}.js'

PROOF_HTML_TITLE_TEMPLATE_VISIT = """ 
    pseudocode.renderElement(
    document.getElementById("{{ id }}"), {
        {% if captionCount %} captionCount: {{ captionCount }} ,{% endif %}
        {% if lineNumber %} lineNumber: true {% endif %}
    });\n
"""


class pseudocode(nodes.General, nodes.Element):
    pass


class pseudocodeContentNode(nodes.General, nodes.Element):
    """Content of pseudocode."""
    pass

class pseudocodeCaption(nodes.caption):
    """Caption of pseudocode."""
    pass

class Pseudocode(SphinxDirective):
    """An environment for pseudocode."""
    has_content = True
    required_arguments = 0
    optional_arguments = 1
    final_argument_whitespace = False
    option_spec = {
        'linenos': directives.unchanged,
        "name": directives.unchanged
    }

    def get_mm_code(self):
        document = self.state.document
        if self.arguments:
            if self.content:
                return [
                    document.reporter.warning(
                        __("Only explicit path supported"), line=self.lineno
                    )
                ]
            argument = search_image_for_language(self.arguments[0], self.env)
            rel_filename, filename = self.env.relfn2path(argument)
            self.env.note_dependency(rel_filename)
            try:
                with open(filename, encoding="utf-8") as fp:
                    code = fp.read()
            except OSError:
                return [
                    document.reporter.warning(
                        __(
                            "External pcode file %r not found or reading "
                            "it failed"
                        )
                        % filename,
                        line=self.lineno,
                    )
                ]
        else:
            code = "\n".join(self.content)
            if not code.strip():
                return [
                    self.state_machine.reporter.warning(
                        __('Ignoring "pcode" directive without content.'),
                        line=self.lineno,
                    )
                ]
        return code

    def run(self):
        node = pseudocode()
        node['code'] = self.get_mm_code()
        
        # Add linenos at the root as well for latex
        if 'linenos' in self.options:
            node['linenos'] = True
            
        node = pseudocode_wrapper(self, node)

        content = pseudocodeContentNode()
        content['code'] = self.get_mm_code()
        content['options'] = {}
        if 'linenos' in self.options:
            content['linenos'] = True

        node += content

        self.add_name(node)
        return [node]


def render_mm_html(self, node, code, options, prefix='pseudocode',
                   imgcls=None, alt=None):
    tag_template = """<pre id="{id}" style="display:hidden;">
            {code}
        </pre>"""
    self.body.append(tag_template.format(id=get_fignumber(self, node), code=self.encode(code)))
    node['id'] = get_fignumber(self, node)


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
        if (pairs['id'] != ''):
            parentId = int(pairs['id'])
            if (parentId > 0):
                parentId -= 1
            functions += jinja2.Template(PROOF_HTML_TITLE_TEMPLATE_VISIT).render(
                id=pairs['id'],
                captionCount=parentId,
                lineNumber=pairs['linenos']
            )

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
    app.add_js_file(f"https://cdn.jsdelivr.net/npm/pseudocode@latest/build/pseudocode.js")
    old_css_add = getattr(app, 'add_stylesheet', None)
    add_css = getattr(app, 'add_css_file', old_css_add)
    add_css(f"https://cdn.jsdelivr.net/npm/pseudocode@latest/build/pseudocode.min.css")
    app.add_js_file(f"https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.11.1/katex.min.js")


def install_js2_part2(app, pagename, templatename, context, doctree):
    """
    Generate katex_autorenderer.js based on ids of each pcode and associated options so that
    we can create associate document.getElementById functions. Then, we register katex_autorenderer.js.
    """
    dicts = []
    if doctree is not None:
        for node in doctree.traverse(pseudocodeContentNode):
            pairs = {'id': node['id'],
                     'linenos': True if 'linenos' in node else False,
                     'parentId': node.parent.attributes.get('ids')[0]}
            dicts.append(pairs)
        if len(dicts) > 0:
            filename_autorenderer_specific = filename_autorenderer.format(
                os.path.split(doctree.attributes.get('source'))[-1].split('.')[0])
            write_katex_autorenderer_file(app, filename_autorenderer_specific, dicts)
            app.add_js_file(filename_autorenderer_specific)


def setup_static_path(app):
    app._katex_static_path = mkdtemp()
    if app._katex_static_path not in app.config.html_static_path:
        app.config.html_static_path.append(app._katex_static_path)


def builder_finished(app, exception):
    # Delete temporary dir used for _static file
    shutil.rmtree(app._katex_static_path)


def pseudocode_wrapper(directive, node, caption=None):
    """Parse caption, and append it to the node."""
    parsed = nodes.Element()
    if caption is None:
        caption_node = pseudocodeCaption()
    else:
        directive.state.nested_parse(
            ViewList([caption], source=""), directive.content_offset, parsed
        )
        caption_node = pseudocodeCaption(parsed[0].rawsource, "", *parsed[0].children)
        caption_node.source = parsed[0].source
        caption_node.line = parsed[0].line
    node += caption_node
    return node


class PseudocodeDomain(StandardDomain):
    """Pseudocode domain"""

    name = "pseudocodecounter"
    label = "Pseudocode Counter"

    directives = {"pseudocode": Pseudocode}


################################################################################
# HTML
def get_fignumber(writer, node):
    """Compute and return the theorem number of `node`."""
    # Copied from the sphinx project: sphinx.writers.html.HTMLTranslator.add_fignumber()
    if not isinstance(node.parent, pseudocode):
        return ""
    figure_id = node.parent["ids"][0]
    key = "pseudocode"
    if figure_id in writer.builder.fignumbers.get(key, {}):
        return ".".join(map(str, writer.builder.fignumbers[key][figure_id]))
    return ""


def html_visit_stuff_node(self, node):
    """Enter :class:`pseudocode` in HTML builder."""
    self.body.append(self.starttag(node, "div", CLASS="pseudocode"))


def html_depart_stuff_node(self, node):
    """Leave :class:`pseudocode` in HTML builder."""
    self.body.append("</div>")


def html_visit_caption_node(self, node):
    """Enter :class:`CaptionNode` in HTML builder."""
    self.body.append(self.starttag(node, "div", CLASS="pseudocode-caption"))
    if node.astext():
        self.body.append(" — ")
        self.body.append(self.starttag(node, "span", CLASS="caption-text"))


def html_depart_caption_node(self, node):
    """Leave :class:`CaptionNode` in HTML builder."""
    if node.astext():
        self.body.append("</span>")
    self.body.append("</div>")


def html_visit_pseudocode_content_node(self, node):
    """Enter :class:`pseudocodeContentNode` in HTML builder."""
    self.body.append(self.starttag(node, "div", CLASS="pseudocode-content"))
    render_mm_html(self, node, node['code'], node['options'])


def html_depart_pseudocode_content_node(self, node):
    """Leave :class:`pseudocodeContentNode` in HTML builder."""
    self.body.append("</div>")

def render_pseudo_latex(self, code: str, lineNumbering: bool, label: str):
    if lineNumbering:
        # Inject line numbering
        code = code.replace("\\begin{algorithmic}", "\\begin{algorithmic}[1]")
    
    # Inject the label at the end of the algorithm
    code = code.replace("\\end{algorithm}", label + "\\end{algorithm}")

    self.body.append(code)

def latex_visit_pseudocode_node(self, node):
    label = self.hypertarget_to(node)
    render_pseudo_latex(self, node['code'], 'linenos' in node, label)
    raise nodes.SkipNode


def setup(app):
    """Setup extension.
    """
    app.add_domain(PseudocodeDomain)

    app.add_enumerable_node(
        pseudocode,
        "pseudocode",
        html=(html_visit_stuff_node, html_depart_stuff_node),
        latex=(latex_visit_pseudocode_node, None)
    )
    app.add_node(
        pseudocodeCaption,
        html=(html_visit_caption_node, html_depart_caption_node),
    )
    app.add_node(
        pseudocodeContentNode,
        html=(html_visit_pseudocode_content_node, html_depart_pseudocode_content_node),
    )

    app.add_directive('pcode', Pseudocode)
    app.config.numfig_format.setdefault('pseudocode', 'Algorithm %s')
    app.connect('builder-inited', builder_inited)
    app.connect('html-page-context', install_js2_part2)
    app.connect('build-finished', builder_finished)

    # Add latex packages
    app.add_latex_package('algorithm')
    app.add_latex_package('algpseudocode')

    return {'version': sphinx.__display_version__, 'parallel_read_safe': True}
