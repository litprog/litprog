```python
# lp_def: aaaa
aaaa = 1111
# lp_include: bbbb
```

```python
# lp_def: bbbb
bbbb = 2222
# lp_include: cccc, aaaa
```

```python
# lp_def: cccc
cccc = 3333
```

```python
# lp_addto: bbbb
bbbb = 2222
# lp_include: cccc
```

```python
# lp_addto: aaaa
import functools
```


```python
# lp_def: slow_fib
def fib(n: int) -> int:
    if n < 2:
        return n
    else:
        return fib(n - 1) + fib(n - 2)
```

```python
# lp_def: imports
from typing import Tuple, List, Dict, Set, Sequence
```

```python
# lp_def: pretty_print_fibs
def pretty_print_fibs(ns: Sequence[int]) -> None:
    """Calculate Fibbonacci numbers and print them to stdout."""
    # lp_include: pretty_print_fibs_impl
```

```python
# lp_exec: python3
# lp_include: imports, slow_fib, pretty_print_fibs
pretty_print_fibs(range(15))
```

```bash
# lp_out
fib( 0) =>   0  fib( 1) =>   1  fib( 2) =>   1
fib( 3) =>   2  fib( 4) =>   3  fib( 5) =>   5
fib( 6) =>   8  fib( 7) =>  13  fib( 8) =>  21
fib( 9) =>  34  fib(10) =>  55  fib(11) =>  89
fib(12) => 144  fib(13) => 233  fib(14) => 377
# exit: 0
```

```python
# lp_addto: imports
import functools
```

```python
# lp_def: pretty_print_fibs_impl
fibs = [fib(n) for n in ns]

pad_n     = len(str(max(ns)))
pad_fib_n = len(str(max(fibs)))

for i, (n, fib_n) in enumerate(zip(ns, fibs)):
    in_str = f"fib({n:>{pad_n}})"
    res_str = f"{fib_n:>{pad_fib_n}}"
    print(f"{in_str} => {res_str}", end ="  ")
    if (i + 1) % 3 == 0:
        print()
```

```python
# lp_run: python -c "print(2 + 3)"
# lp_expect: 0
5
# exit: 0
```
