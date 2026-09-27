"""Ring polynomial multiplication, coefficient sampling, and norm checks."""

from __future__ import annotations

import math
import random
from collections.abc import Sequence


def sample_gaussian(dimension: int, sigma: float, seed: int | None = None) -> list[int]:
    """Sample rounded Gaussian coefficients with a local random generator."""
    if dimension <= 0 or sigma <= 0:
        raise ValueError("dimension and sigma must be positive")
    rng = random.Random(seed)
    return [round(rng.gauss(0.0, sigma)) for _ in range(dimension)]


def within_l2_bound(coefficients: Sequence[int], bound: float) -> bool:
    """Check the Euclidean norm against a supplied bound."""
    return math.sqrt(sum(value * value for value in coefficients)) <= bound


def negacyclic_multiply(a: Sequence[int], b: Sequence[int], modulus: int) -> list[int]:
    """Multiply in Z_q[x]/(x^d + 1) using a direct coefficient loop."""
    if not a or len(a) != len(b):
        raise ValueError("Polynomials must have the same nonzero dimension")
    if modulus <= 1:
        raise ValueError("modulus must exceed one")
    degree = len(a)
    result = [0] * degree
    for i, left in enumerate(a):
        for j, right in enumerate(b):
            index = i + j
            sign = 1 if index < degree else -1
            result[index % degree] += sign * left * right
    return [coefficient % modulus for coefficient in result]
