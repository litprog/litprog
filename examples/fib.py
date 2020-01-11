

def fib(n: int) -> int:
    if n < 2:
        return n 
    else:
        return fib(n - 1) + fib(n - 2)
for i in range(10):
    print(fib(i), end=" ")