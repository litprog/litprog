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
val=     0.001044122 log= -2.98125 sig=5   r=.00104
val=     0.092275536 log= -1.03491 sig=4   r=.0923
val=     0.326008443 log= -0.48677 sig=3   r=.326
val=     0.652326130 log= -0.18554 sig=3   r=.652
val=     0.656500401 log= -0.18277 sig=3   r=.657
val=     1.052429478 log=  0.02219 sig=2   r=1.05
val=     1.804832985 log=  0.25644 sig=2   r=1.8
val=     4.005683972 log=  0.60268 sig=2   r=4.01
val=     5.565885113 log=  0.74553 sig=2   r=5.57
val=   167.277951833 log=  2.22344 sig=0   r=167.
# exit: 0
```
