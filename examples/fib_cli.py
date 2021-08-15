#!/usr/bin/env python
import os, sys, math, time
import contextlib
from typing import Sequence
__doc__ = f"""Usage: python {__file__} [--help] [--pretty] <n>..."""
def fib(n: int) -> int:
    if n < 2:
        return n
    else:
        return fib(n - 1) + fib(n - 2)
_cache: dict[int, int] = {}
def fast_fib(n: int) -> int:
    if n < 2:
        return n
    elif n in _cache:
        return _cache[n]
    else:
        _cache[n] = fast_fib(n - 1) + fast_fib(n - 2)
        return _cache[n]
def pretty_print_fibs(ns: Sequence[int]) -> None:
    """Calculate Fibbonacci numbers and print them to stdout."""
    fibs = [fib(n) for n in ns]
    pad_n     = len(str(max(ns)))
    pad_fib_n = len(str(max(fibs)))
    for i, (n, fib_n) in enumerate(zip(ns, fibs)):
        in_str = f"fib({n:>{pad_n}})"
        res_str = f"{fib_n:>{pad_fib_n}}"
        print(f"{in_str} => {res_str}", end="  ")
        if (i + 1) % 3 == 0:
            print()
ParamsAndFlags = tuple[list[str], set[str]]
def parse_args(args: list[str]) -> ParamsAndFlags:
    flags = {arg for arg in args if arg.startswith("-")}
    params = [arg for arg in args if arg not in flags]
    return params, flags
def main(args: list[str] = sys.argv[1:]) -> int:
    params, flags = parse_args(args)
    if not args or "--help" in flags or "-h" in flags:
        print(__doc__)
        return 0
    invalid_params = [n for n in params if not n.isdigit()]
    if any(invalid_params):
        print("Invalid parameters: ", invalid_params)
        return 1
    ns = [int(n) for n in params]
    if "-p" in flags or "--pretty" in flags:
        pretty_print_fibs(ns)
    else:
        for n in ns:
            print(fast_fib(n))
    return 0
if __name__ == '__main__':
    sys.exit(main())