Test :eq: inside pcode
----------------------

.. math::
   :label: my-equation

   a^2 + b^2 = c^2

.. pcode::

   \begin{algorithm}
   \caption{Algorithm that references an equation}
   \begin{algorithmic}
   \STATE compute the value using :eq:`my-equation`
   \end{algorithmic}
   \end{algorithm}

.. pcode::

   \begin{algorithm}
   \caption{Algorithm with undefined equation}
   \begin{algorithmic}
   \STATE see :eq:`no-such-equation`
   \end{algorithmic}
   \end{algorithm}
