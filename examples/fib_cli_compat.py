#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
try:
    import builtins
except ImportError:
    import __builtin__ as builtins
import itertools
str = getattr(builtins, 'unicode', str)
zip = getattr(itertools, 'izip', zip)
__doc__ = 'Usage: python {0} [--help] [--pretty] <n>...'.format(__file__)
import sys
from typing import List, Set, Tuple
from typing import Dict
_fib_cache = {}


def fast_fib(n):
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


def pretty_print_fibs(ns):
    fibs = [fib(n) for n in ns]
    pad_n = len(str(max(ns)))
    pad_fib_n = len(str(max(fibs)))
    for i, (n, fib_n) in enumerate(zip(ns, fibs)):
        in_str = 'fib({0:>{1}})'.format(n, pad_n)
        res_str = '{0:>{1}}'.format(fib_n, pad_fib_n)
        print('{0} => {1}'.format(in_str, res_str), end='  ')
        if (i + 1) % 3 == 0:
            print()


ParamsAndFlags = Tuple[List[str], Set[str]]


def parse_args(args):
    flags = {arg for arg in args if arg.startswith('-')}
    params = [arg for arg in args if arg not in flags]
    return params, flags


def main(args=sys.argv[1:]):
    params, flags = parse_args(args)
    if not args or '--help' in flags or '-h' in flags:
        print(__doc__)
        return 0
    invalid_params = [n for n in params if not n.isdigit()]
    if any(invalid_params):
        print('Invalid parameters: ', invalid_params)
        return 1
    ns = [int(n) for n in params]
    if '-p' in flags or '--pretty' in flags:
        pretty_print_fibs(ns)
    else:
        for n in ns:
            print(fib(n))
    return 0


if __name__ == '__main__':
    sys.exit(main())

