
def isprime(n):
    """Returns True if n is prime."""
    if n == 2:
        return True
    if n == 3:
        return True
    if n % 2 == 0:
        return False
    if n % 3 == 0:
        return False

    i = 5
    w = 2

    while i * i <= n:
        if n % i == 0:
            return False

        i += w
        w = 6 - w

    return True


print(isprime(491623273481))
import re

num_re = re.compile(r"""
    (\d{4})\s/\s\d+
""", re.VERBOSE)

nums_data = open("teldata.txt").read()
nums = [
    int(num.group(0).replace(" ", "").replace("/", "").lstrip("0"))
    for num in num_re.finditer(nums_data)
]

oldnums = set(line.strip() for line in open("allnums.txt"))
allnums = set()

for num in nums:
    allnums.add(str(num))

    print(("old" if (str(num) in oldnums) else "new").rjust(16))
    print(int(isprime(num)), str(num).rjust(16))
    num = int("49" + str(num))
    print(int(isprime(num)), str(num).rjust(16))
    print()

allnums.update(oldnums)
open("allnums.txt", mode='w').write("\n".join(sorted(allnums)))
