from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import List, Tuple, Union


class Globals:
    """Meant to be used as a type checked dictionary"""
    named_consts: Tuple[str, ...] = ('e', 'pi')
    e: Decimal = Decimal((0, (2, 7, 1, 8, 2, 8, 1, 8), -7))
    pi: Decimal = Decimal((0, (3, 1, 4, 1, 5, 9, 2, 6), -7))
    unary_operators: List[str] = ['-', 'sqrt', 'log', 'log10', 'exp', 'sin', 'cos', 'tan', 'sec', 'cosec', 'cot']
    binary_operators: List[str] = ['+', '-', '*', '/', '^']


class AbstractExpression(ABC):
    @abstractmethod
    def __eq__(self, other) -> bool:
        pass

    @abstractmethod
    def __repr__(self):
        pass

    @abstractmethod
    def __str__(self):
        pass

    @abstractmethod
    def dx(self, wrt: Var) -> AbstractExpression:
        """Return the differential of the current expression wrt to the parameter 'wrt'"""
        pass

    def simplify(self) -> AbstractExpression:
        """Try to simplify the current expression using some simple rules"""
        return self


class Const(AbstractExpression):
    def __init__(self, value: Union[int, str, Decimal]):
        if isinstance(value, str) and value in Globals.named_consts:
            value = Globals.__dict__[value]
        self._value: Decimal = Decimal(value)

    def __eq__(self, other) -> bool:
        if not isinstance(other, Const):
            return False
        return self._value == other._value

    def __repr__(self):
        return f"Const({self._value!r})"

    def __str__(self):
        for const in Globals.named_consts:
            if self._value == Globals.__dict__[const]:
                return const
        return str(self._value)

    def __add__(self, other: Const) -> Const:
        return Const(self._value + other._value)

    def __sub__(self, other: Const) -> Const:
        return Const(self._value - other._value)

    def __mul__(self, other: Const) -> Const:
        return Const(self._value * other._value)

    def __truediv__(self, other: Const) -> Const:
        return Const(self._value / other._value)

    def __pow__(self, other: Const) -> Const:
        return Const(self._value ** other._value)

    def ln(self) -> Const:
        """Return the base e logarithm as a Const"""
        return Const(self._value.ln())

    def dx(self, wrt) -> Const:
        return Const(0)


class Var(AbstractExpression):
    def __init__(self, identifier: str):
        self._identifier: str = identifier

    def __eq__(self, other) -> bool:
        if not isinstance(other, Var):
            return False
        return self._identifier == other._identifier

    def __repr__(self):
        return f"Var({self._identifier!r})"

    def __str__(self):
        return self._identifier

    def dx(self, wrt) -> Const:
        if self == wrt:
            return Const(1)
        else:
            return Const(0)
