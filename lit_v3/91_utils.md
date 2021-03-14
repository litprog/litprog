# Utility Functions

Pure/functional/stateless utility code.


## Math Utilities

Round to `n` significant digits.

```python
# def: sig_round
import math

def sig_round(val: float, n: int = 3) -> float:
    if n <= 1:
        raise TypeError(f"n must be > 0, but got n={repr(n)}")

    if val == 0.0:
        return 0.0

    log = math.log10(abs(val))
    if log <= 1.5:
        sig = -int(log - n)
    else:
        sig = -int(log - (n - 1))

    return round(val, sig)
```

```python
# exec
# dep: sig_round
assert sig_round(123.456, n=3) == 123.0
assert sig_round(123.456, n=2) == 120.0
assert sig_round( 23.456, n=3) ==  23.5
assert sig_round(  3.456, n=3) ==   3.46
assert sig_round(  0.456, n=3) ==   0.456
assert sig_round(  0.456, n=2) ==   0.46
```

Fuzz test `sig_round`.

```python
# exec
# dep: sig_round
import random

# deterministic random so we don't needlessly change output
rand = random.Random(0)

for _ in range(1000):
    sign = rand.choice([1, -1])
    abs_val = (0.5 + rand.random()) ** rand.randint(1, 15)
    abs_val = max(0.0001, min(1000, abs_val))
    val = sign * abs_val
    n = rand.randint(2, 7)
    sig_val = sig_round(val, n)
    sig_val_str = str(sig_val).replace(".", "").strip("-0")
    eps = 50 * abs_val / (10 ** n)
    delta = abs(val - sig_val)
    # print(f"{val=:<28} {n=} {sig_val=:<9} {eps=:18.9f} {delta=:18.9f}")
    assert abs(val - sig_val) < eps
    assert len(sig_val_str) <= n
```
