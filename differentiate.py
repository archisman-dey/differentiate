from base import AbstractExpression, Globals, Var
from input_parser import Parser

print("Available functions: ", end='')
print(*Globals.unary_operators, sep=', ', end = '\n\n')

print("Use x, y, or z as variables.", end = '\n\n')

print("Also, if there is a digit just after '-', it is always interpreted as a negative number, "
    "so something like '2-1' should be written as '2 - 1'", end = '\n\n')

input_string = input("Differentiate: ")
var = Var(input("with respect to: ").strip())
expression: AbstractExpression = Parser(input_string).parse()
print("Input parsed as: ", expression)
print("Result: ", expression.dx(var).simplify())
