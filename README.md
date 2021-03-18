# Differentiate

Differentiate any given expression.

This is something I wrote while learning about context free grammars, parsing, and so on. It is written in object oriented Python.

An article I found very helpful: [Parsing Expressions by Recursive Descent](https://www.engr.mun.ca/~theo/Misc/exp_parsing.htm)

## How to run

`python3 differentiate.py`

(tested with python 3.8 under Linux and Windows)

## Examples

    archisman@acerswift3:~/code/python/differentiate$ py differentiate.py 
    Available functions: -, sqrt, log, log10, exp, sin, cos, tan, sec, cosec, cot

    Use x, y, or z as variables.

    Differentiate: sqrt(tan(x)) + sin(x)*cos(x)          
    with respect to: x
    Input parsed as:  (sqrt(tan(x))+(sin(x)*cos(x)))
    Result:  (((0.5/sqrt(tan(x)))*(sec(x)^2))+((sin(x)*(-sin(x)))+(cos(x)*cos(x))))
