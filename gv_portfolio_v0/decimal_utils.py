"""Context-independent Decimal serialization for operated portfolio records."""

from __future__ import annotations

from contextlib import contextmanager
from decimal import Decimal
from typing import Iterator

MAX_DECIMAL_INTEGER_DIGITS = 64
MAX_DECIMAL_FRACTION_DIGITS = 64
DETERMINISTIC_DECIMAL_PRECISION = 256
DETERMINISTIC_DECIMAL_EXPONENT_LIMIT = 256


@contextmanager
def deterministic_decimal_context() -> Iterator[None]:
    """Run bounded portfolio arithmetic independently of caller Decimal settings."""

    from decimal import localcontext

    with localcontext() as context:
        context.prec = DETERMINISTIC_DECIMAL_PRECISION
        context.Emin = -DETERMINISTIC_DECIMAL_EXPONENT_LIMIT
        context.Emax = DETERMINISTIC_DECIMAL_EXPONENT_LIMIT
        context.clamp = 0
        for signal in context.traps:
            context.traps[signal] = True
        yield


def decimal_text(value: Decimal) -> str:
    """Render a finite Decimal without consulting the ambient Decimal context."""

    if not isinstance(value, Decimal) or not value.is_finite():
        raise ValueError("FINITE_DECIMAL_REQUIRED")
    sign, digits, exponent = value.as_tuple()
    coefficient_digits = list(digits)
    if not coefficient_digits or all(digit == 0 for digit in coefficient_digits):
        return "0"
    while len(coefficient_digits) > 1 and coefficient_digits[-1] == 0:
        coefficient_digits.pop()
        exponent += 1
    integer_digits = len(coefficient_digits) + max(exponent, 0)
    fraction_digits = max(-exponent, 0)
    if (
        integer_digits > MAX_DECIMAL_INTEGER_DIGITS
        or fraction_digits > MAX_DECIMAL_FRACTION_DIGITS
    ):
        raise ValueError("DECIMAL_OUT_OF_BOUNDS")
    coefficient = "".join(str(digit) for digit in coefficient_digits)
    if exponent >= 0:
        text = coefficient + ("0" * exponent)
    else:
        split = len(coefficient) + exponent
        if split <= 0:
            text = "0." + ("0" * -split) + coefficient
        else:
            text = coefficient[:split] + "." + coefficient[split:]
    return f"-{text}" if sign else text
