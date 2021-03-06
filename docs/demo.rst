.. _hello-world-algo:
.. pcode::
   :linenos:

    \begin{algorithmic}
    \PRINT \texttt{'hello world'}
    \end{algorithmic}

.. _quick-sort:
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

.. pcode::

    \begin{algorithm}
    \caption{Test text-style}
    \begin{algorithmic}
    \REQUIRE some preconditions
    \ENSURE some postconditions
    \INPUT some inputs
    \OUTPUT some outputs
    \PROCEDURE{Test-Declarations}{}
        \STATE font families: {\sffamily sffamily, \ttfamily ttfamily, \normalfont normalfont, \rmfamily rmfamily.}
        \STATE font weights: {normal weight, \bfseries bold, \mdseries
        medium, \lfseries lighter. }
        \STATE font shapes: {\itshape itshape \scshape Small-Caps \slshape slshape \upshape upshape.}
        \STATE font sizes: \tiny tiny \scriptsize scriptsize \footnotesize
        footnotesize \small small \normalsize normal \large large \Large Large
        \LARGE LARGE \huge huge \Huge Huge \normalsize
    \ENDPROCEDURE
    \PROCEDURE{Test-Commands}{}
        \STATE \textnormal{textnormal,} \textrm{textrm,} \textsf{textsf,} \texttt{texttt.}
        \STATE \textbf{textbf,} \textmd{textmd,} \textlf{textlf.}
        \STATE \textup{textup,} \textit{textit,} \textsc{textsc,} \textsl{textsl.}
        \STATE \uppercase{uppercase,} \lowercase{LOWERCASE.}
    \ENDPROCEDURE
    \PROCEDURE{Test-Colors}{}
    % feature not implemented
    \ENDPROCEDURE
    \end{algorithmic}
    \end{algorithm}

.. pcode::

    \begin{algorithm}
    \caption{Test atoms}
    \begin{algorithmic}
    \STATE \textbf{Specials:} \{ \} \$ \& \# \% \_
    \STATE \textbf{Bools:} \AND \OR \NOT \TRUE \FALSE
    \STATE \textbf{Carriage return:} first line \\ second line
    \STATE \textbf{Text-symbols:} \textbackslash
    \STATE \textbf{Quote-symbols:} `single quotes', ``double quotes''
    \STATE \textbf{Math:} $(\mathcal{C}_m)$, $i \gets i + 1$, $E=mc^2$, \( x^n + y^n = z^n \), $\$$, \(\$\)
    \END{ALGORITHMIC}
    \END{ALGORITHM}

.. _test-control-blocks:
.. pcode::

    \begin{algorithm}
    \caption{Test control blocks}
    \begin{algorithmic}
    \PROCEDURE{Test-If}{}
        \IF{ <cond>}
            \STATE <block>;
        \ELIF{<cond>}
            \STATE <block>;
        \ELSE
            \STATE <block>;
        \ENDIF
    \ENDPROCEDURE
    \PROCEDURE{Test-For}{$n$}
        \STATE $i \gets 0$
        \FOR{$i < n$}
            \PRINT $i$
            \STATE $i \gets i + 1$
        \ENDFOR
    \ENDPROCEDURE
    \PROCEDURE{Test-For-To}{$n$}
        \STATE $i \gets 0$
        \FOR{$i$ \TO $n$}
            \PRINT $i$
        \ENDFOR
    \ENDPROCEDURE
    \PROCEDURE{Test-For-DownTo}{$n$}
        \FOR{$i \gets n$ \DOWNTO $0$}
            \PRINT $i$
        \ENDFOR
    \ENDPROCEDURE
    \PROCEDURE{Test-For-All}{$n$}
        \FORALL{$i \in \{0, 1, \cdots, n\}$}
            \PRINT $i$
        \ENDFOR
    \ENDPROCEDURE
    \PROCEDURE{Test-While}{$n$}
        \STATE $i \gets 0$
        \WHILE{$i < n$}
            \PRINT $i$
            \STATE $i \gets i + 1$
        \ENDWHILE
    \ENDPROCEDURE
    \PROCEDURE{Test-Repeat}{$n$}
        \STATE $i \gets 0$
        \REPEAT
            \PRINT $i$
            \STATE $i \gets i + 1$
        \UNTIL{$i>n$}
    \ENDPROCEDURE
    \PROCEDURE{Test-Break-Continue}{$n$}
        \FOR{$i = 0$ \TO $2n$}
            \IF{$i < n/2$}
                \CONTINUE
            \ELIF{$i > n$}
                \BREAK
            \ENDIF
            \PRINT $i$
        \ENDFOR
    \ENDPROCEDURE
    \end{algorithmic}
    \end{algorithm}

.. pcode::

    \begin{algorithm}
    \caption{Test statements and comments}
    \begin{algorithmic}
    \PROCEDURE{Test-Statements}{}
        \STATE This line is a normal statement
        \PRINT \texttt{`this is print statement'}
        \RETURN $retval$
    \ENDPROCEDURE

    \PROCEDURE{Test-Comments}{} \COMMENT{comment for procedure}
        \STATE a statement \COMMENT{inline comment}
        \STATE \COMMENT{line comment}
        \IF{some condition}\COMMENT{comment for if}
            \RETURN \TRUE \COMMENT{another inline comment}
        \ELSE \COMMENT{comment for else}
            \RETURN \FALSE \COMMENT{yet another inline comment}
        \ENDIF
    \ENDPROCEDURE
    \end{algorithmic}
    \end{algorithm}

.. pcode::

    % This quicksort algorithm is extracted from Chapter 7, Introduction
    % to Algorithms (3rd edition)
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
                $A[i]$ with $A[j]$
            \ENDIF
            \STATE exchange $A[i]$ with $A[r]$
        \ENDFOR
    \ENDPROCEDURE
    \end{algorithmic}
    \end{algorithm}