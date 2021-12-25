****************************************
Welcome to Sphinxcontrib-pseudocode demo
****************************************

.. toctree::
   :maxdepth: 2
   :caption: Contents:

########
Features
########

Below shows various rendered algorithms, which are copied from corresponding `pseudocode.js examples <https://github.com/SaswatPadhi/pseudocode.js/blob/master/static/body.html.part>`__.
The source code of those algorithms can be found `here <https://github.com/xxks-kkk/sphinxcontrib-pseudocode/blob/master/docs/demo.rst>`__.

We can also reference any particular algorithm. For example, we can also reference each algorithm:

- ``:numref:`quick-sort``` produces :numref:`quick-sort`
- ``:numref:`Here is my algorithm {number} <quick-sort>``` produces :numref:`Here is my algorithm {number} <quick-sort>`
- ``:ref:`test control blocks <test-control-blocks>``` produces :ref:`test control blocks <test-control-blocks>`

By default, each ``pcode`` is mapped to 'Algorithm %s' when referenced via ``numref``. You can change this
behavior by overriding the corresponding string of ``'pseudocode'`` key in `numfig_format <https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-numfig_format>`_.

.. include:: demo.rst

##########
Limitation
##########

- If there are more than :math:`\LaTeX` algorithm block within a ``pcode`` directive::

    \begin{algorithm}
    \caption{Test atoms}
    \begin{algorithmic}
    \STATE my algorithm 1
    \END{ALGORITHMIC}
    \END{ALGORITHM}

  The numbering of the algorithm and the numbering when you reference it will out of sync.
  As an example, ``:numref:`test-control-blocks``` shows :numref:`test-control-blocks` but
  the algorithm is actually numbered with 5. The reason is that both Algorithm 3 and 4
  are within the same ``pcode`` directive. If there is only one :math:`\LaTeX` algorithm block
  for each ``pcode`` directive, there is no problem.