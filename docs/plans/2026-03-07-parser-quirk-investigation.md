# Investigation: reStructuredText Parser Quirk

**Date:** 2026-03-07

## Goal

To identify the root cause of the issue where `pcode` directive blocks were being ignored by the parser if their content started with a `
ewcommand` definition.

## Initial Hypothesis

The initial hypothesis was that the `docutils` parser was fundamentally misinterpreting any content block that began with a backslash (``) character, potentially treating it as a special marker and therefore failing to recognize it as valid directive content.

## Investigation Steps

1.  **Isolate from Sphinx:** To determine if the issue was specific to Sphinx or was deeper within `docutils`, a minimal test script was created. This script defined a simple custom directive and used `docutils.core.publish_string` to parse a basic reStructuredText string.

2.  **Minimal Test Case:** The test used two strings: one where the directive's content started with `hello` and another where it started with `\hello`.

    ```python
    # Simplified for documentation
    from docutils.core import publish_string, directives
    from docutils.parsers.rst import Directive

    class MyDirective(Directive):
        has_content = True
        def run(self):
            print(f"Content: {self.content}")
            return []

    directives.register_directive('mydirective', MyDirective)

    publish_string(".. mydirective::

   \hello")
    ```

3.  **Result of Minimal Test:** The test script successfully parsed the content in both cases, printing `Content: ['\hello']`. This **disproved the initial hypothesis** that any block starting with a backslash was problematic.

4.  **Re-evaluating the Failure:** The test failure in the `pytest-sphinx` environment was re-examined. The error was `WARNING: Ignoring "pcode" directive without content.` This pointed to the `self.content` of the directive being empty.

5.  **Escape Sequence Hypothesis:** The next hypothesis was that the issue was not the backslash itself, but the specific sequence of characters. In reStructuredText, a backslash is an escape character. In the string `
ewcommand`, the sequence `\c` is not a standard escape sequence, and this might be what was confusing the parser.

6.  **Verification:** This was tested by escaping the backslash in the test `.rst` file (i.e., using `
ewcommand`). With the backslash escaped, the tests passed. This confirmed that the parser's escape sequence handling was the root of the problem.

## Root Cause

The reStructuredText parser (`docutils`) treats a backslash followed by any character as an "escape sequence".

- When the parser encounters `\c` in `
ewcommand`, it's an unrecognized escape sequence. This appears to disrupt the parser's state, causing it to fail to correctly identify the content of the directive block.
- When a comment line (`% ...`) is added before `
ewcommand`, the line with the backslash is no longer the first thing the parser sees in the content block, and it handles it correctly.
- When the backslash is escaped (`
ewcommand`), the parser correctly interprets it as a literal backslash and passes the correct string to the directive.

## Design Implication: Why Preamble-Only Stripping Cannot Work

The implementation plan originally proposed extracting `\newcommand` only from a
strict preamble — lines at the very top of the pcode content, before any
non-`\newcommand` line. This approach is incompatible with the RST quirk:

- The RST quirk **forces** users to add `% comment` before any leading `\newcommand`.
- A strict preamble treats `% comment` as a non-`\newcommand` line and ends the
  preamble immediately, so the `\newcommand` that follows is never extracted.
- Result: inline macros are completely unusable.

The two constraints are fundamentally incompatible:

```
RST quirk forces:    % comment \n \newcommand{\foo}{...}
Strict preamble sees: % comment → preamble ends → \newcommand NOT stripped
```

The correct implementation strips `\newcommand` from **any position** in the pcode
content, regardless of what precedes it. This is the only approach that works
end-to-end for users following the documented workaround.

## Solution and Final Decision

While the root cause lies within `docutils`, modifying the behavior of the upstream parser is outside the scope of this extension.

The chosen solution is to document this behavior and provide a simple, reliable workaround for users.

1.  **Documentation:** The documentation was updated to instruct users to not start a `pcode` block directly with `
ewcommand`.
2.  **Workaround:** The official recommendation is to add a comment line (e.g., `% A comment`) before the first `
ewcommand` if it's at the start of a block.
3.  **Tests:** The test suite was updated to include this comment, ensuring the tests pass and validating the documented workaround.
