"""Fibonacci Test."""


def fib(num: int) -> int:
    """Fibonacci test."""
    return num if num < 2 else fib(num - 1) + fib(num - 2)
