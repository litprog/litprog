# Scratchpad

```python
# def: values
import math, random

rand = random.Random(1)

values = sorted([
    # int((rand.random() - 0.5) * 2) *    # sign
    (0.5 + rand.random()) ** rand.randint(1, 15)
    for _ in range(9)
])

while 0.0 in values:
    values.remove(0.0)
```

```python
# exec: python3
# dep: values
n = 4
for val in values:
    log = math.ceil(math.log10(abs(val)))
    m = n - log
    r = round(val, m)
    print(f"{val=:16.9f} {log=:9.5f} {n=} {m=} {r=:<9}")
```

```shell
# out
val=     0.000132092 log= -3.00000 n=4 m=7 r=0.0001321
val=     0.001708999 log= -2.00000 n=4 m=6 r=0.001709
val=     0.064542477 log= -1.00000 n=4 m=5 r=0.06454
val=     0.105655775 log=  0.00000 n=4 m=4 r=0.1057
val=     0.311147990 log=  0.00000 n=4 m=4 r=0.3111
val=     1.262280082 log=  1.00000 n=4 m=3 r=1.262
val=     1.695894290 log=  1.00000 n=4 m=3 r=1.696
val=     6.264509594 log=  1.00000 n=4 m=3 r=6.265
val=     6.391712289 log=  1.00000 n=4 m=3 r=6.392
# exit: 0
```
