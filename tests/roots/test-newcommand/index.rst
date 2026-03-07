.. pcode::
   :linenos:

   % comment
   \newcommand{\floor}[1]{\lfloor #1 \rfloor}

   \begin{algorithm}
   \caption{Using an Inline Macro}
   \begin{algorithmic}
   \STATE The floor of 3.14 is $\floor{3.14}$.
   \end{algorithmic}
   \end{algorithm}

.. math::

   \newcommand{\ceil}[1]{\lceil #1 \rceil}

.. pcode::

   \begin{algorithm}
   \caption{Using a Per-Page Macro}
   \begin{algorithmic}
   \STATE The ceiling of 3.14 is $\ceil{3.14}$.
   \end{algorithmic}
   \end{algorithm}

.. pcode::

   \begin{algorithm}
   \caption{Using a Global Macro}
   \begin{algorithmic}
   \STATE The set of real numbers is $\RR$.
   \end{algorithmic}
   \end{algorithm}
