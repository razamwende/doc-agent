"""Module de test pour les fixtures."""

def add(a: int, b: int) -> int:
    """Additionne deux entiers."""
    return a + b


def undocumented_function(x, y, z):
    result = x * y + z
    return result


class Calculator:
    """Calculatrice simple."""

    def __init__(self, precision: int = 2):
        self.precision = precision

    def multiply(self, a: float, b: float) -> float:
        return round(a * b, self.precision)

    def undocumented_method(self, val):
        return val ** 2
