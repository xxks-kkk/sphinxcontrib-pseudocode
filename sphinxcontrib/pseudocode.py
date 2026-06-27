# -*- coding: utf-8 -*-
"""
    sphinx-pseudocode
    ~~~~~~~~~~~~~~~~~

    Allow typeset algorithms in latex powered by pseudocode.js inside sphinx-doc

    :copyright: Copyright 2021 by Zeyuan Hu.
    :license: BSD, see LICENSE for details.
"""

import json
import os
import re
from textwrap import dedent

import jinja2
import sphinx
from docutils import nodes
from docutils.nodes import make_id
from docutils.parsers.rst import Directive, directives
from docutils.statemachine import ViewList
from sphinx.domains.std import StandardDomain
from sphinx.util import logging

logger = logging.getLogger(__name__)

mapname_re = re.compile(r'<map id="(.*?)"')

_NEWCOMMAND_RE = re.compile(
    r'\\newcommand\{(\\[^}]+)\}(?:\[(\d+)\])?\{((?:[^{}]|\{[^{}]*\})*)\}'
)

_REF_PATTERN = re.compile(r':ref:`([^`<]+?)(?:\s*<([^>]+)>)?`')

_EQ_PATTERN = re.compile(r':eq:`([^`<]+?)(?:\s*<([^>]+)>)?`')

filename_autorenderer = 'pseudocode_autorenderer_{}.js'

PROOF_HTML_TITLE_TEMPLATE_VISIT = """
    (function() {
        var pcsEl = document.getElementById("{{ id }}");
        {% if ref_replacements_json %}
        var pcsContainer = pcsEl ? pcsEl.parentElement : null;
        {% endif %}
        pseudocode.renderElement(pcsEl, {
            captionCount: {{ captionCount }},
            {% if lineNumber %} lineNumber: true {% endif %}
        });
        {% if ref_replacements_json %}
        if (pcsContainer) {
            var refs = {{ ref_replacements_json }};
            var html = pcsContainer.innerHTML;
            refs.forEach(function(r) {
                html = html.split(r.placeholder).join('<a href="' + r.href + '">' + r.text + '</a>');
            });
            pcsContainer.innerHTML = html;
        }
        {% endif %}
    })();
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
        
        content['code'] = '\n'.join(code_lines)
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
    
    all_macros = node.get('page_macros', []) + node.get('inline_macros', [])
    
    if all_macros:
        macros_str = '\n'.join(all_macros)
        hidden_div = f'<div style="display:none;">\\[\n{macros_str}\n\\]</div>'
        self.body.append(hidden_div)

    tag_template = """<pre id="{id}" style="display:none;">
            {code}
        </pre>"""
    self.body.append(tag_template.format(id=get_fignumber(self.builder, node), code=self.encode(code)))
    node['id'] = get_fignumber(self.builder, node)











def write_pseudocode_autorenderer_file(app, filename, dicts, all_macros=None):
    outdir = os.path.join(app.builder.outdir, '_static')
    os.makedirs(outdir, exist_ok=True)
    filepath = os.path.join(outdir, filename)
    content = pseudocode_autorenderer_content(app, dicts, all_macros)
    with open(filepath, 'w') as file:
        file.write(content)


def pseudocode_autorenderer_content(app, dicts, all_macros=None):
    functions = ''
    for pairs in dicts:
        if (pairs['id'] != ''):
            ref_replacements = pairs.get('ref_replacements', [])
            functions += jinja2.Template(PROOF_HTML_TITLE_TEMPLATE_VISIT).render(
                id=pairs['id'],
                lineNumber=pairs['linenos'],
                captionCount=pairs.get('captionCount', 0),
                ref_replacements_json=json.dumps(ref_replacements) if ref_replacements else ''
            )

    # Convert \newcommand strings to MathJax tex.macros format so macros are
    # configured before MathJax initialises (the autorenderer is synchronous;
    # MathJax is deferred, so it reads window.MathJax on startup).
    mathjax_macros = {}
    for macro_str in (all_macros or []):
        m = _NEWCOMMAND_RE.match(macro_str.strip())
        if m:
            cmd, nargs, body = m.groups()
            cmd_name = cmd[1:]  # strip leading backslash
            mathjax_macros[cmd_name] = [body, int(nargs)] if nargs else body

    sync_macro_init = ''
    if mathjax_macros:
        macros_json = json.dumps(mathjax_macros)
        sync_macro_init = (
            'window.MathJax = window.MathJax || {};\n'
            'window.MathJax.tex = window.MathJax.tex || {};\n'
            # Existing user macros (from mathjax3_config) take priority over ours.
            f'window.MathJax.tex.macros = Object.assign({macros_json}, window.MathJax.tex.macros || {{}});\n'
        )

    content = dedent('''\
            {sync_macro_init}document.addEventListener("DOMContentLoaded", function() {{
              var renderAll = function() {{
                {functions}
                if (typeof MathJax !== 'undefined' && MathJax.typesetPromise) {{
                  MathJax.typesetPromise();
                }}
              }};
              if (typeof MathJax !== 'undefined' && MathJax.startup) {{
                MathJax.startup.promise.then(renderAll);
              }} else {{
                renderAll();
              }}
            }});''')

    content = content.format(functions=functions, sync_macro_init=sync_macro_init)
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


def _resolve_refs_in_code(code, docname, app):
    """Replace :ref: and :eq: roles in pcode content with placeholders.

    pseudocode.js renders the pcode content verbatim, so Sphinx roles never
    get resolved by the normal pipeline.  We substitute each role with a
    unique PCSREF<N> token that a JS post-processor swaps back for an <a> tag.

    Returns (modified_code, replacements) where replacements is a list of
    dicts with keys 'placeholder', 'text', 'href' for JS post-processing.
    """
    std_labels = app.env.domaindata.get('std', {}).get('labels', {})
    replacements = []

    def add_replacement(text, href):
        placeholder = f'PCSREF{len(replacements)}'
        replacements.append({'placeholder': placeholder, 'text': text, 'href': href})
        return placeholder

    def replace_ref(m):
        display = m.group(1).strip()
        target = (m.group(2) or display).strip().lower()
        href = '#'
        if target in std_labels:
            target_docname, labelid, _ = std_labels[target]
            try:
                href = app.builder.get_relative_uri(docname, target_docname)
                if labelid:
                    href += '#' + labelid
            except Exception:
                pass
        else:
            logger.warning(
                "pcode: undefined label %r in :ref: role (in document %r)",
                target, docname,
                type='ref', subtype='ref',
                location=docname,
            )
        return add_replacement(display, href)

    def replace_eq(m):
        # The math domain ignores any explicit display text for :eq: and always
        # renders the equation number, so the target is the only thing we need.
        target = (m.group(2) or m.group(1)).strip()
        text, href = _resolve_eq(target, docname, app)
        return add_replacement(text, href)

    modified_code = _REF_PATTERN.sub(replace_ref, code)
    modified_code = _EQ_PATTERN.sub(replace_eq, modified_code)
    return modified_code, replacements


def _resolve_eq(target, docname, app):
    """Resolve an :eq: target to (link_text, href).

    Mirrors sphinx.domains.math.MathDomain.resolve_xref so the rendered link
    matches a :eq: used in ordinary prose: the text is the formatted equation
    number and the href points at the equation anchor.
    """
    env = app.env
    equations = env.get_domain('math').equations  # labelid -> (docname, number)

    if target not in equations:
        logger.warning(
            "pcode: equation not found: %r in :eq: role (in document %r)",
            target, docname,
            type='ref', subtype='eq',
            location=docname,
        )
        return target, '#'

    target_docname, number = equations[target]
    node_id = make_id('equation-%s' % target)

    if getattr(env.config, 'math_numfig', False) and env.config.numfig:
        if target_docname in env.toc_fignumbers:
            toc_dm = env.toc_fignumbers[target_docname].get('displaymath', {})
            numbers = toc_dm.get(node_id, ())
            eqno = '.'.join(map(str, numbers))
            numsep = getattr(env.config, 'math_numsep', '.')
            eqno = numsep.join(eqno.rsplit('.', 1))
        else:
            eqno = ''
    else:
        eqno = str(number)

    eqref_format = env.config.math_eqref_format or '({number})'
    try:
        text = eqref_format.format(number=eqno)
    except (KeyError, IndexError):
        text = '(%s)' % eqno

    href = '#'
    try:
        href = app.builder.get_relative_uri(docname, target_docname)
        if node_id:
            href += '#' + node_id
    except Exception:
        pass

    return text, href


def doctree_resolved(app, doctree, docname):
    """Extract \\newcommand from math blocks and attach to pcode nodes."""
    page_macros = []
    for math_node in doctree.findall(nodes.math_block):
        content = math_node.astext()
        for raw in _NEWCOMMAND_RE.findall(content):
            cmd, nargs, body = raw
            if nargs:
                page_macros.append(f'\\newcommand{{{cmd}}}[{nargs}]{{{body}}}')
            else:
                page_macros.append(f'\\newcommand{{{cmd}}}{{{body}}}')

    for content_node in doctree.findall(pseudocodeContentNode):
        content_node['page_macros'] = list(page_macros)
        if hasattr(app.builder, 'get_relative_uri'):
            modified_code, replacements = _resolve_refs_in_code(
                content_node['code'], docname, app
            )
            if replacements:
                content_node['code'] = modified_code
                content_node['ref_replacements'] = replacements


def install_js2_part2(app, pagename, templatename, context, doctree):
    if not doctree:
        return

    # Generate and register autorenderer
    dicts = []
    seen_macros = set()
    all_macros = []
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
                     'captionCount': caption_count,
                     'ref_replacements': node.get('ref_replacements', [])}
            dicts.append(pairs)
            for m in (node.get('page_macros', []) + node.get('inline_macros', [])):
                if m not in seen_macros:
                    seen_macros.add(m)
                    all_macros.append(m)

    if len(dicts) > 0:
        filename_autorenderer_specific = filename_autorenderer.format(
            os.path.split(doctree.attributes.get('source'))[-1].split('.')[0])
        write_pseudocode_autorenderer_file(app, filename_autorenderer_specific, dicts, all_macros)
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
