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
from textwrap import dedent

import jinja2
import sphinx
from docutils import nodes
from docutils.parsers.rst import Directive, directives
from docutils.statemachine import ViewList
from sphinx.domains.std import StandardDomain
from sphinx.util import logging

logger = logging.getLogger(__name__)

mapname_re = re.compile(r'<map id="(.*?)"')

_NEWCOMMAND_RE = re.compile(
    r'\\newcommand\{(\\[^}]+)\}(?:\[(\d+)\])?\{((?:[^{}]|\{[^{}]*\})*)\}'
)


def _parse_brace_group(s: str, pos: int) -> tuple[str, int]:
    """Parse a {}-delimited group starting at pos (which must be '{').

    Returns (content_without_braces, end_pos_after_closing_brace).
    Handles arbitrarily nested braces.
    """
    assert s[pos] == '{'
    depth = 0
    pos += 1
    start = pos
    while pos < len(s):
        if s[pos] == '{':
            depth += 1
        elif s[pos] == '}':
            if depth == 0:
                return s[start:pos], pos + 1
            depth -= 1
        pos += 1
    return s[start:], len(s)


def _expand_macro_call(code: str, cmd: str, nargs: int, body: str) -> str:
    """Replace all occurrences of ``cmd`` (with its ``nargs`` brace arguments)
    in *code* with the expanded *body*, substituting ``#1``, ``#2``, … for the
    matched arguments.  Leaves unrecognised call sites untouched.
    """
    pattern = re.compile(re.escape(cmd) + r'(?![a-zA-Z@])')
    result: list[str] = []
    i = 0
    while i < len(code):
        m = pattern.search(code, i)
        if not m:
            result.append(code[i:])
            break
        result.append(code[i:m.start()])
        pos = m.end()
        if nargs == 0:
            result.append(body)
            i = pos
        else:
            args: list[str] = []
            tmp = pos
            ok = True
            for _ in range(nargs):
                while tmp < len(code) and code[tmp] in ' \t\n':
                    tmp += 1
                if tmp >= len(code) or code[tmp] != '{':
                    ok = False
                    break
                arg, tmp = _parse_brace_group(code, tmp)
                args.append(arg)
            if ok:
                expanded = body
                for j, arg in enumerate(args):
                    expanded = expanded.replace(f'#{j + 1}', arg)
                result.append(expanded)
                i = tmp
            else:
                result.append(code[m.start():m.end()])
                i = m.end()
    return ''.join(result)


def _expand_newcommands(code_lines: list[str], macros: list[str]) -> str:
    """Expand ``\\newcommand`` macros in *code_lines* and return the resulting
    code string (without the ``\\newcommand`` definition lines).

    Each macro defined in *macros* is applied in order; later macros can refer
    to earlier ones in their bodies.
    """
    macro_defs: list[tuple[str, int, str]] = []
    for line in macros:
        m = _NEWCOMMAND_RE.search(line)
        if m:
            cmd, nargs_str, body = m.groups()
            macro_defs.append((cmd, int(nargs_str) if nargs_str else 0, body))

    code = '\n'.join(code_lines)
    for cmd, nargs, body in macro_defs:
        code = _expand_macro_call(code, cmd, nargs, body)
    return code

filename_autorenderer = 'pseudocode_autorenderer_{}.js'

PROOF_HTML_TITLE_TEMPLATE_VISIT = """
    pseudocode.renderElement(
    document.getElementById("{{ id }}"), {
        captionCount: {{ captionCount }},
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

class Pseudocode(Directive):
    """An environment for pseudocode."""
    has_content = True
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {
        'linenos': directives.unchanged
    }

    def get_mm_code(self):
        pcode = '\n'.join(self.content)
        if not pcode.strip():
            return [self.state_machine.reporter.warning(
                'Ignoring "pcode" directive without content.',
                line=self.lineno)]
        return pcode

    def run(self):
        all_code = self.get_mm_code()
        if not isinstance(all_code, str):
            # It's a warning list, return it
            return all_code

        caption_match = re.search(r'\\caption\{([^}]+)\}', all_code)
        caption = caption_match.group(1) if caption_match else None

        node = pseudocode()
        node['code'] = all_code
        node = pseudocode_wrapper(self, node, caption)

        content = pseudocodeContentNode()

        lines = all_code.split('\n')
        macros = []
        code_lines = []
        for line in lines:
            if line.strip().startswith('\\newcommand'):
                macros.append(line)
            else:
                code_lines.append(line)

        content['code'] = _expand_newcommands(code_lines, macros)
        content['inline_macros'] = macros
        content['page_macros'] = []  # filled in by doctree-resolved handler

        content['options'] = {}
        if 'linenos' in self.options:
            content['linenos'] = True

        node += content

        self.add_name(node)
        return [node]


def render_mm_html(self, node, code, options, prefix='pseudocode',
                   imgcls=None, alt=None):

    tag_template = """<pre id="{id}" style="display:none;">
            {code}
        </pre>"""
    self.body.append(tag_template.format(id=get_fignumber(self.builder, node), code=self.encode(code)))
    node['id'] = get_fignumber(self.builder, node)


def write_pseudocode_autorenderer_file(app, filename, dicts):
    outdir = os.path.join(app.builder.outdir, '_static')
    os.makedirs(outdir, exist_ok=True)
    filepath = os.path.join(outdir, filename)
    content = pseudocode_autorenderer_content(app, dicts)
    with open(filepath, 'w') as file:
        file.write(content)


def pseudocode_autorenderer_content(app, dicts):
    content = dedent('''\
            document.addEventListener("DOMContentLoaded", function() {{
              var renderAll = async function() {{
                if (typeof MathJax !== 'undefined' && MathJax.typesetPromise) {{
                  await MathJax.typesetPromise();
                }}
                {functions}
              }};
              if (typeof MathJax !== 'undefined' && MathJax.startup) {{
                MathJax.startup.promise.then(renderAll);
              }} else {{
                renderAll();
              }}
            }});''')
    functions = ''
    for pairs in dicts:
        if (pairs['id'] != ''):
            functions += jinja2.Template(PROOF_HTML_TITLE_TEMPLATE_VISIT).render(
                id=pairs['id'],
                lineNumber=pairs['linenos'],
                captionCount=pairs.get('captionCount', 0)
            )

    content = content.format(functions=functions)
    return content


def builder_inited(app):
    install_js(app)


def builder_finished(app, exception):
    pass

def install_js(app, *args):
    app.add_js_file("https://cdn.jsdelivr.net/npm/pseudocode@latest/build/pseudocode.js")
    old_css_add = getattr(app, 'add_stylesheet', None)
    add_css = getattr(app, 'add_css_file', old_css_add)
    add_css("https://cdn.jsdelivr.net/npm/pseudocode@latest/build/pseudocode.min.css")


def doctree_resolved(app, doctree, docname):
    """Extract \\newcommand from math blocks, expand them in pcode nodes at build time."""
    page_macro_lines = []
    for math_node in doctree.findall(nodes.math_block):
        content = math_node.astext()
        for raw in _NEWCOMMAND_RE.findall(content):
            cmd, nargs, body = raw
            if nargs:
                page_macro_lines.append(f'\\newcommand{{{cmd}}}[{nargs}]{{{body}}}')
            else:
                page_macro_lines.append(f'\\newcommand{{{cmd}}}{{{body}}}')

    for content_node in doctree.findall(pseudocodeContentNode):
        content_node['page_macros'] = []
        if page_macro_lines:
            code_lines = content_node['code'].split('\n')
            content_node['code'] = _expand_newcommands(code_lines, page_macro_lines)


def install_js2_part2(app, pagename, templatename, context, doctree):
    if not doctree:
        return

    # Generate and register autorenderer
    dicts = []
    if doctree:
        for node in doctree.findall(pseudocodeContentNode):
            fig_id = get_fignumber(app.builder, node)
            # captionCount seeds pseudocode.js's counter to fignumber-1 so it
            # increments to fignumber, matching Sphinx's :numref: value.
            try:
                caption_count = int(fig_id.split('.')[-1]) - 1
            except (ValueError, AttributeError):
                caption_count = 0
            pairs = {'id': fig_id,
                     'linenos': True if 'linenos' in node else False,
                     'captionCount': caption_count}
            dicts.append(pairs)

    if len(dicts) > 0:
        filename_autorenderer_specific = filename_autorenderer.format(
            os.path.split(doctree.attributes.get('source'))[-1].split('.')[0])
        write_pseudocode_autorenderer_file(app, filename_autorenderer_specific, dicts)
        app.add_js_file(filename_autorenderer_specific)


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
def get_fignumber(builder, node):
    """Compute and return the theorem number of `node`."""
    # Copied from the sphinx project: sphinx.writers.html.HTMLTranslator.add_fignumber()
    if not isinstance(node.parent, pseudocode) or not node.parent['ids']:
        return ""
    figure_id = node.parent["ids"][0]
    key = "pseudocode"
    if figure_id in builder.fignumbers.get(key, {}):
        return ".".join(map(str, builder.fignumbers[key][figure_id]))
    return ""


def html_visit_stuff_node(self, node):
    """Enter :class:`pseudocode` in HTML builder."""
    self.body.append(self.starttag(node, "div", CLASS="pseudocode"))


def html_depart_stuff_node(self, node):
    """Leave :class:`pseudocode` in HTML builder."""
    self.body.append("</div>")


def html_visit_caption_node(self, node):
    """Enter :class:`CaptionNode` in HTML builder.
    Emit nothing — pseudocode.js renders the \\caption{} visually inside the
    algorithm box.  The node still lives in the doctree so Sphinx fignumbers
    machinery can number it for :numref: cross-references.
    """
    raise nodes.SkipNode


def html_depart_caption_node(self, node):
    """Leave :class:`CaptionNode` in HTML builder."""
    pass


def html_visit_pseudocode_content_node(self, node):
    """Enter :class:`pseudocodeContentNode` in HTML builder."""
    self.body.append(self.starttag(node, "div", CLASS="pseudocode-content"))
    render_mm_html(self, node, node['code'], node['options'])


def html_depart_pseudocode_content_node(self, node):
    """Leave :class:`pseudocodeContentNode` in HTML builder."""
    self.body.append("</div>")


def setup(app):
    """Setup extension.
    """
    app.add_domain(PseudocodeDomain)

    app.add_enumerable_node(
        pseudocode,
        "pseudocode",
        html=(html_visit_stuff_node, html_depart_stuff_node),
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
    app.connect('doctree-resolved', doctree_resolved)
    app.connect('html-page-context', install_js2_part2)
    app.connect('build-finished', builder_finished)

    return {'version': sphinx.__display_version__, 'parallel_read_safe': True}
