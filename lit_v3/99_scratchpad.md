# Scratchpad

```python
# exec: python3
import math, random

values = sorted([
    # int((random.random() - 0.5) * 2) *    # sign
    (0.5 + random.random()) ** random.randint(1, 15)
    for _ in range(10)
])

while 0.0 in values:
    values.remove(0.0)

n = 3
for val in values:
    log = math.log10(abs(val))
    if log < 1:
        sig = - int(log - n)
    else:
        sig = - int(log - (n - 1))

    r = str(round(val, sig)).strip("0")
    print(f"{val=:16.9f} {log=:9.5f} {sig=:<3} {r=:<9}")
```

```shell
# out
val=     0.010247823 log= -1.98937 sig=4   r=.0102
val=     0.013693799 log= -1.86348 sig=4   r=.0137
val=     0.156158292 log= -0.80643 sig=3   r=.156
val=     0.266994840 log= -0.57350 sig=3   r=.267
val=     0.796885444 log= -0.09860 sig=3   r=.797
val=     1.018396883 log=  0.00792 sig=2   r=1.02
val=     2.645714209 log=  0.42254 sig=2   r=2.65
val=     4.217550699 log=  0.62506 sig=2   r=4.22
val=     4.332112988 log=  0.63670 sig=2   r=4.33
val=    27.004916629 log=  1.43144 sig=0   r=27.
# exit: 0
```
