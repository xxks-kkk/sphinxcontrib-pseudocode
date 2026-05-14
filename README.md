# sphinxcontrib-pseudocode

This is a [sphinx-doc](https://www.sphinx-doc.org/en/master/) extension that allows you to write LaTeX algorithm
directly inside sphinx-doc. The rendering of LaTex algorithm is powered by 
[pseudocode.js](https://github.com/SaswatPadhi/pseudocode.js).

## Demo

You can directly type LaTeX algorithm (e.g., quicksort algorithm taken from pseudocode.js demo) under ``pcode``
directive in any `.rst` files as follows:

```text
.. pcode::
   :linenos:

    % This quicksort algorithm is extracted from Chapter 7, Introduction to Algorithms (3rd edition)
    \begin{algorithm}
    \caption{Quicksort}
    \begin{algorithmic}
    \PROCEDURE{Quicksort}{$A, p, r$}
        \IF{$p < r$}
            \STATE $q = $ \CALL{Partition}{$A, p, r$}
            \STATE \CALL{Quicksort}{$A, p, q - 1$}
            \STATE \CALL{Quicksort}{$A, q + 1, r$}
        \ENDIF
    \ENDPROCEDURE
    \PROCEDURE{Partition}{$A, p, r$}
        \STATE $x = A[r]$
        \STATE $i = p - 1$
        \FOR{$j = p$ \TO $r - 1$}
            \IF{$A[j] < x$}
                \STATE $i = i + 1$
                \STATE exchange
                $A[i]$ with     $A[j]$
            \ENDIF
            \STATE exchange $A[i]$ with $A[r]$
        \ENDFOR
    \ENDPROCEDURE
    \end{algorithmic}
    \end{algorithm}
```

The above code will be rendered as 

![quicksort-demo](https://raw.githubusercontent.com/xxks-kkk/sphinxcontrib-pseudocode/master/tests/roots/test-basic/_static/quicksort-demo.png)

See more examples on [demo page](https://zhu45.org/sphinxcontrib-pseudocode/).

## Installation and Configuration

Install the package via 

```
pip install sphinxcontrib-pseudocode
```

Then in the Sphinx-doc ``conf.py``, add

```python
extensions = [
    'sphinx.ext.mathjax',
    'sphinxcontrib.pseudocode'
]
```

**MathJax version requirement:** The current release of pseudocode.js (`@latest`, v2.4.1)
requires `MathJax.tex2chtml`, which was removed in MathJax 4. Sphinx 8+ defaults to
MathJax 4, so you must pin MathJax 3 explicitly in your ``conf.py``:

```python
mathjax_path = 'https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js'
```

Without this setting, algorithm blocks containing math expressions will silently fail
to render in any Sphinx version that defaults to MathJax 4.

> **Note:** MathJax 4 support has been merged into pseudocode.js but not yet released
> ([commit 1ab6334](https://github.com/SaswatPadhi/pseudocode.js/commit/1ab63342dba3a046b258fae54132c5cfd32987b5)).
> Once a new version is published to npm, the `mathjax_path` pin can be removed.

## Usage

Write LaTeX algorithm within ``pcode`` directive as shown above. The following option is supported:

- ``linenos`` (``LineNumber`` in pseudocode.js: Whether line numbering is enabled)

## For Developer

This [blog](https://zhu45.org/posts/2021/Dec/21/release-of-sphinxcontrib-pseudocode/) explains the underlying implementation details of this extension.
