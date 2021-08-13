# Scratchpad

```python
# exec: python3
import math, random

values = sorted([
    # int((random.random() - 0.5) * 2) *    # sign
    (0.5 + random.random()) ** random.randint(1, 15)
    for _ in range(9)
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
val=     0.002322099 log= -2.63412 sig=5   r=.00232
val=     0.108896252 log= -0.96299 sig=3   r=.109
val=     0.230594382 log= -0.63715 sig=3   r=.231
val=     0.738482548 log= -0.13166 sig=3   r=.738
val=     0.754110956 log= -0.12256 sig=3   r=.754
val=     0.978454728 log= -0.00946 sig=3   r=.978
val=     1.237576359 log=  0.09257 sig=2   r=1.24
val=     4.477051772 log=  0.65099 sig=2   r=4.48
val=     4.783445398 log=  0.67974 sig=2   r=4.78
# exit: 0
```
