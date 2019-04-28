#!/usr/bin/env python
__doc__ = f"""Usage: python {__file__} [--help] [--pretty] <n>..."""

import sys
from typing import List, Set, Tuple


from typing import Dict

_fib_cache: Dict[int, int] = {}

def fast_fib(n: int) -> int:
    if n <= 1:
        return n

    if n in _fib_cache:
        return _fib_cache[n]

    _fib_cache[n - 2] = fast_fib(n - 2)
    _fib_cache[n - 1] = fast_fib(n - 1)
    assert n - 1 in _fib_cache, n
    return _fib_cache[n - 1] + _fib_cache[n - 2]
fib = fast_fib

from typing import Sequence 

def pretty_print_fibs(ns: Sequence[int]) -> None:
    fibs = [fib(n) for n in ns]

    pad_n     = len(str(max(ns)))
    pad_fib_n = len(str(max(fibs)))

    for n, fib_n in zip(ns, fibs):
        in_str = f"fib({n:>{pad_n}})"
        res_str = f"{fib_n:>{pad_fib_n}}"
        print(f"{in_str} => {res_str}", end ="  ")
        if (n + 1) % 3 == 0: 
            print()


def parse_args(args: List[str]) -> Tuple[List[str], Set[str]]:
    flags = {arg for arg in args if arg.startswith("-")}
    params = [arg for arg in args if arg not in flags]
    return params, flags

def main(args: List[str] = sys.argv[1:]) -> int:
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
            print(fib(n))
    return 0


if __name__ == '__main__':
    sys.exit(main())