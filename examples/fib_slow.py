print("starting")
def fib(n: int) -> int:
    if n < 2:
        return n
    else:
        return fib(n - 1) + fib(n - 2)
fibs = [fib(n) for n in range(9)]
assert fibs == [0, 1, 1, 2, 3, 5, 8, 13, 21]
assert fib(12) == 144
assert fib(20) == fib(19) + fib(18)
print("fibs:", fibs)
print("complete")