def fib(n: int) -> int:
    if n < 2:
        return n
    else:
        return fib(n - 1) + fib(n - 2)
for i in range(12):
    print(f"fib({i:>2}) -> {fib(i):>3}  ", end=" ")
    if (i + 1) % 3 == 0:
        print()