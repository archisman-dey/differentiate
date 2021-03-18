from __future__ import annotations

import decimal
import re
from decimal import Decimal
from itertools import chain
from typing import List, Union

from base import AbstractExpression, Const, Globals, Var
from expressions import BinaryExpression, UnaryExpression


"""
    [] -> Optional
    {} -> One or More
    | -> Or

    sign = '+' | '-'
    digits = '0' | '1' | ... | '9'
    integer = [sign] {digits}
    decimal = [sign] {digits} '.' {digits}

    NUM: integer | decimal
    VAR: 'x' | 'y' | 'z'

    T = NUM | VAR
    BRAC = '(' | ')'

    U: all unary operators
    B: all binary operators

    Grammar =
    E --> P [{B P}]
    P --> T | '(' E ')' | U P
"""


class BadInput(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class Token:
    def __init__(self, value: str):
        self.value: str = value

    def __eq__(self, other) -> bool:
        if not isinstance(other, Token):
            return False
        return self.value == other.value

    def __bool__(self) -> bool:
        return bool(self.value)

    def __repr__(self):
        return f"<Token: {self.value}>"

    def __str__(self):
        return self.value

    def is_binary_operator(self) -> bool:
        return self.value in Globals.binary_operators

    def is_unary_operator(self) -> bool:
        return self.value in Globals.unary_operators

    def is_const(self) -> bool:
        # named const
        if self.value in Globals.named_consts:
            return True

        # num
        try:
            Decimal(self.value)
        except decimal.InvalidOperation:
            return False
        else:
            return True

    def is_var(self) -> bool:
        # var
        if self.value in 'xyz':
            return True

        return False

    def is_terminal(self) -> bool:
        return self.is_const() or self.is_var()


class Lexer:
    # regular expression for numbers, copied from stack overflow
    _num_pattern: re.Pattern = re.compile(r'(?!-0?(\.0+)?$)-?(0|[1-9]\d*)?(\.\d+)?(?<=\d)')

    def __init__(self, input_string: str):
        self.string: str = input_string
        self.current_index: int = 0

    def consume(self) -> Token:
        """get next token while advancing through the string"""
        next_token = self.peek()
        if next_token:
            self.current_index += len(next_token.value)
        return next_token

    def peek(self) -> Token:
        """get next token without advancing through the string"""
        if self.current_index >= len(self.string):
            return Token("")

        if self.string[self.current_index].isspace():
            self.current_index += 1
            return self.peek()

        # num
        match = Lexer._num_pattern.match(self.string[self.current_index:])
        if match:
            return Token(match.group())

        # brac
        if self.string[self.current_index] in ['(', ')']:
            return Token(self.string[self.current_index])

        # operators
        for op in chain(Globals.unary_operators, Globals.binary_operators):
            if self.string.startswith(op, self.current_index):
                return Token(op)

        # replace ** with ^
        if self.string.startswith("**", self.current_index):
            return Token('^')

        # named consts
        for const in Globals.named_consts:
            if self.string.startswith(const, self.current_index):
                return Token(const)

        # var
        if self.string[self.current_index] in 'xyz':
            return Token(self.string[self.current_index])

        raise BadInput(f"Lexer failed at index: {self.current_index} in input: {self.string}")


class BaseOperator:
    def __init__(self):
        # Object of BaseOperator is used as sentinel
        self.op = None

    def __repr__(self):
        return f'{type(self): {self.op}}'

    def __gt__(self, other: BaseOperator) -> bool:
        """Compare operators by precedence and associativity"""
        if isinstance(self, BinaryOperator) and isinstance(other, BinaryOperator):
            precedence = {'^': 3, '*': 2, '/': 2, '+': 1, '-': 1}
            return precedence[self.op] >= precedence[other.op]

        if isinstance(self, UnaryOperator) and isinstance(other, BinaryOperator):
            return True

        if isinstance(other, UnaryOperator):
            return False

        if type(self) == BaseOperator:
            return False

        raise ValueError(f"Comparison between {self} and {other} not implemented")


class BinaryOperator(BaseOperator):
    def __init__(self, op: Token):
        super().__init__()
        if not op.is_binary_operator():
            raise ValueError("Invalid Binary Operator")
        self.op: str = op.value


class UnaryOperator(BaseOperator):
    def __init__(self, op: Token):
        super().__init__()
        if not op.is_unary_operator():
            raise ValueError("Invalid Unary Operator")
        self.op: str = op.value


class Parser:
    def __init__(self, input_string: str):
        self.lexer: Lexer = Lexer(input_string)

        self.operator_stack: List[BaseOperator] = []
        self.operand_stack: List[AbstractExpression] = []

    def expect(self, token: Token):
        if self.lexer.peek() == token:
            self.lexer.consume()
        else:
            raise BadInput(f"Unexpected token at index: {self.lexer.current_index}, expected: {token}, "
                           f"got: {self.lexer.peek()}")

    @staticmethod
    def make_terminal(token: Token) -> Union[Const, Var]:
        if token.is_const():
            return Const(token.value)
        elif token.is_var():
            return Var(token.value)

        raise BadInput(f"Invalid token passed to make_terminal : {token}")

    @staticmethod
    def make_unary_expression(operator: UnaryOperator, operand: AbstractExpression) -> AbstractExpression:
        return UnaryExpression(operator.op, operand).simplify()

    @staticmethod
    def make_binary_expression(operator: BinaryOperator, operand1: AbstractExpression,
                               operand2: AbstractExpression) -> AbstractExpression:
        return BinaryExpression(operand1, operator.op, operand2).simplify()

    def pop_operator(self):
        operator: BaseOperator = self.operator_stack.pop()

        if isinstance(operator, BinaryOperator):
            operand2: AbstractExpression = self.operand_stack.pop()
            operand1: AbstractExpression = self.operand_stack.pop()

            self.operand_stack.append(self.make_binary_expression(operator, operand1, operand2))
       
        elif isinstance(operator, UnaryOperator):
            self.operand_stack.append(self.make_unary_expression(operator, self.operand_stack.pop()))
        
        else:
            raise ValueError("pop_operator called for sentinel")

    def push_operator(self, operator: BaseOperator):
        while self.operator_stack[-1] > operator:
            self.pop_operator()
        self.operator_stack.append(operator)

    def parse_e(self):
        self.parse_p()

        while self.lexer.peek().is_binary_operator():
            self.push_operator(BinaryOperator(self.lexer.consume()))
            self.parse_p()

        while type(self.operator_stack[-1]) != BaseOperator:  # while top is not sentinel
            self.pop_operator()

    def parse_p(self):
        next_token = self.lexer.peek()

        if next_token.is_terminal():
            self.operand_stack.append(self.make_terminal(self.lexer.consume()))

        elif next_token == Token('('):
            self.lexer.consume()
            self.operator_stack.append(BaseOperator())  # sentinel
            self.parse_e()
            self.expect(Token(')'))
            self.operator_stack.pop()  # pops the sentinel

        elif next_token.is_unary_operator():
            self.push_operator(UnaryOperator(self.lexer.consume()))
            self.parse_p()

        else:
            raise BadInput(f"Invalid Syntax at index: {self.lexer.current_index}")

    def parse(self):
        self.operator_stack.append(BaseOperator())  # used as sentinel
        self.parse_e()
        self.expect(Token(""))

        assert len(self.operand_stack) == 1, "Stack still has more than one element"
        return self.operand_stack[0]
