from __future__ import annotations

from decimal import Decimal

from base import AbstractExpression, Const, Globals


class UnaryExpression(AbstractExpression):
    def __init__(self, operator, operand: AbstractExpression):
        self.operand = operand.simplify()
        if operator not in Globals.unary_operators:
            raise ValueError(f"No such Unary Operator: '{operator}'")
        self.operator = operator

    def __eq__(self, other) -> bool:
        if not isinstance(other, UnaryExpression):
            return False
        return self.operator == other.operator and self.operand.simplify() == other.operand.simplify()

    def __repr__(self):
        return f"UnaryExp({self.operator!r}, {self.operand!r})"

    def __str__(self):
        if self.operator == '-':
            return f"(-{self.operand})"
        else:
            return f"{self.operator}({self.operand})"

    def dx(self, wrt):
        switch = {
            # -x -> -1
            '-': lambda: Const(-1),
            # sqrt(x) -> 1/2 / sqrt(x)
            'sqrt': lambda: BinaryExpression(Const(Decimal(1 / 2)), '/', self),
            # log (ln) x -> 1 / x
            'log': lambda: BinaryExpression(Const(1), '/', self.operand),
            # log10 x -> log10(e) / x
            'log10': lambda: BinaryExpression(Const(Globals.e.log10()), '/', self.operand),
            # exp x -> exp x
            'exp': lambda: self,
            # sin x -> cos x
            'sin': lambda: UnaryExpression('cos', self.operand),
            # cos x -> -(sin x)
            'cos': lambda: UnaryExpression('-', UnaryExpression('sin', self.operand)),
            # tan x -> (sec x) ^ 2
            'tan': lambda: BinaryExpression(UnaryExpression('sec', self.operand), '^', Const(2)),
            # sec x -> sec x * tan x
            'sec': lambda: BinaryExpression(self, '*', UnaryExpression('tan', self.operand)),
            # cosec x -> - cosec x * cot x
            'cosec': lambda: UnaryExpression('-', BinaryExpression(self, '*',
                                                                   UnaryExpression('cot', self.operand))),
            # cot x -> - (cosec x) ^ 2
            'cot': lambda: UnaryExpression('-', BinaryExpression(
                UnaryExpression('cosec', self.operand), '^', Const(2)))
        }

        return BinaryExpression(switch[self.operator](), '*', self.operand.dx(wrt)).simplify()

    def simplify(self) -> AbstractExpression:
        return self


class BinaryExpression(AbstractExpression):
    def __init__(self, left: AbstractExpression, operator, right: AbstractExpression):
        self.left = left.simplify()
        self.right = right.simplify()
        if operator not in Globals.binary_operators:
            raise ValueError(f"No such Binary Operator: '{operator}'")
        self.operator = operator

    def __eq__(self, other) -> bool:
        if not isinstance(other, BinaryExpression):
            return False
        if self.operator != other.operator:
            return False

        if self.operator in ['+', '*']:
            return ((self.left == other.left and self.right == other.right) or
                    (self.left == other.right and self.right == other.left))
        else:
            return self.left == other.left and self.right == other.right

    def __repr__(self):
        return f"BinaryExp({self.left!r}, {self.operator!r}, {self.right!r})"

    def __str__(self):
        return f"({self.left}{self.operator}{self.right})"

    def dx(self, wrt):
        if self.operator == '^':
            if isinstance(self.right, Const):
                # x^c -> c * x^(c-1)
                exponent = BinaryExpression(self.left, '^', BinaryExpression(self.right, '-', Const(1)))
                return BinaryExpression(self.right, '*', exponent).simplify()
            elif isinstance(self.left, Const):
                # c^x = exp(x log c) -> log_c * c^x
                log_c = self.left.ln()
                return BinaryExpression(log_c, '*', self).simplify()
            else:
                raise NotImplementedError("Variable base and exponent not yet implemented!")

        switch = {
            # x + y -> dx + dy
            '+': lambda: BinaryExpression(self.left.dx(wrt), '+', self.right.dx(wrt)),
            # x - y -> dx - dy
            '-': lambda: BinaryExpression(self.left.dx(wrt), '-', self.right.dx(wrt)),
            # xy -> xdy + ydx
            '*': lambda: BinaryExpression(BinaryExpression(self.left, '*', self.right.dx(wrt)), '+',
                                          BinaryExpression(self.right, '*', self.left.dx(wrt))),
            # x/y -> (ydx - xdy) / y^2
            '/': lambda: BinaryExpression(
                BinaryExpression(BinaryExpression(self.right, '*', self.left.dx(wrt)), '-',
                                 BinaryExpression(self.left, '*', self.right.dx(wrt))),
                '/', BinaryExpression(self.right, '^', Const(2))),
        }
        return switch[self.operator]().simplify()

    def simplify(self):
        # const op const = const
        if isinstance(self.left, Const) and isinstance(self.right, Const):
            switch = {
                '+': lambda: self.left + self.right,
                '-': lambda: self.left - self.right,
                '*': lambda: self.left * self.right,
                '/': lambda: self.left / self.right,
                '^': lambda: self.left ** self.right
            }
            return switch[self.operator]()
        # 0 + x = x
        if self.operator == '+':
            if self.left == Const(0):
                return self.right
            if self.right == Const(0):
                return self.left

        # 0 - x = -x, x - 0 = x
        if self.operator == '-':
            if self.left == Const(0):
                return UnaryExpression('-', self.right)
            if self.right == Const(0):
                return self.left
        # 0 * x = 0
        # 1 * x = x
        if self.operator == '*':
            if Const(0) in [self.left, self.right]:
                return Const(0)
            if self.left == Const(1):
                return self.right
            if self.right == Const(1):
                return self.left
        # 0 / {x\0} = 0, x / 1 = x
        if self.operator == '/':
            if self.right == Const(0):
                raise ValueError("Division by Zero")
            if self.left == Const(0):
                return Const(0)
            if self.right == Const(1):
                return self.left
        # x^0 = 1, x^1 = x
        if self.operator == '^':
            if self.right == Const(0):
                return Const(1)
            if self.right == Const(1):
                return self.left

        return self
