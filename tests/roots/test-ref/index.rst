Test :ref: inside pcode
-----------------------

.. _base-algorithm:

.. pcode::

   \begin{algorithm}
   \caption{Base Algorithm}
   \begin{algorithmic}
   \STATE do something
   \end{algorithmic}
   \end{algorithm}

.. pcode::

   \begin{algorithm}
   \caption{Derived Algorithm}
   \begin{algorithmic}
   \STATE extends :ref:`Base Algorithm <base-algorithm>`
   \end{algorithmic}
   \end{algorithm}

.. pcode::

   \begin{algorithm}
   \caption{Algorithm with undefined ref}
   \begin{algorithmic}
   \STATE see :ref:`Nonexistent Algorithm <no-such-label>`
   \end{algorithmic}
   \end{algorithm}

.. _sec-multiple-strings:

Extending to Multiple Strings
-----------------------------

.. pcode::

   \begin{algorithm}
   \caption{Algorithm with bare section ref}
   \begin{algorithmic}
   \STATE as described in :ref:`sec-multiple-strings`
   \end{algorithmic}
   \end{algorithm}
