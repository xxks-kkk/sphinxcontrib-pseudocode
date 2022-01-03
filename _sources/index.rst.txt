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

.. note::

    We assume each ``pcode`` directive contains exactly one :math:`\LaTeX` algorithmic block::

        \begin{algorithm}
        \caption{Test atoms}
        \begin{algorithmic}
        \STATE my algorithm 1
        \END{ALGORITHMIC}
        \END{ALGORITHM}

    You still can have multiple algorithmic blocks but the numbering will be messed up.

By default, each ``pcode`` is mapped to 'Algorithm %s' when referenced via ``numref``. You can change this
behavior by overriding the corresponding string of ``'pseudocode'`` key in `numfig_format <https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-numfig_format>`_.

.. include:: demo.rst