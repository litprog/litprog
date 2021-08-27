## Appendix

### Boilerplate

```python
# def: boilerplate
from typing import Optional, Iterator

DIGITS = "123456789"
```

Test case for `grid_items`.

```python
# exec: python3
# dep: grid_items, fixtures
assert dict(grid_items(FIXTURE_1)) == {
    "A1": "4", "A2": ".", "A3": ".",
    "A4": ".", "A5": ".", "A6": ".",
    "A7": "8", "A8": ".", "A9": "5",
    "B1": ".", "B2": "3", "B3": ".",
    "B4": ".", "B5": ".", "B6": ".",
    "B7": ".", "B8": ".", "B9": ".",
    "C1": ".", "C2": ".", "C3": ".",
    "C4": "7", "C5": ".", "C6": ".",
    "C7": ".", "C8": ".", "C9": ".",

    "D1": ".", "D2": "2", "D3": ".",
    "D4": ".", "D5": ".", "D6": ".",
    "D7": ".", "D8": "6", "D9": ".",
    "E1": ".", "E2": ".", "E3": ".",
    "E4": ".", "E5": "8", "E6": ".",
    "E7": "4", "E8": ".", "E9": ".",
    "F1": ".", "F2": ".", "F3": ".",
    "F4": ".", "F5": "1", "F6": ".",
    "F7": ".", "F8": ".", "F9": ".",

    "G1": ".", "G2": ".", "G3": ".",
    "G4": "6", "G5": ".", "G6": "3",
    "G7": ".", "G8": "7", "G9": ".",
    "H1": "5", "H2": ".", "H3": ".",
    "H4": "2", "H5": ".", "H6": ".",
    "H7": ".", "H8": ".", "H9": ".",
    "I1": "1", "I2": ".", "I3": "4",
    "I4": ".", "I5": ".", "I6": ".",
    "I7": ".", "I8": ".", "I9": ".",
}
```

The `shorten_digits` function is just to make the output of the `display` function a bit less verbose for partially solved puzzles. It's primary use is during debugging/develpment.

### Pretty Printing

```python
# def: shorten_digits
def shorten_digits(digits: str) -> str:
    """Shorten contiguous sequences of digits."""
    for i in range(8):
        for j in range(9, i - 1, -1):
            if j - i < 3:
                continue
            r = "".join(map(str, range(i, j + 1)))
            if r in digits:
                digits = digits.replace(r, r[0] + "-" + r[-1])
    return digits
```

```python
# exec: python3
# dep: shorten_digits
assert shorten_digits("12345")     == "1-5"
assert shorten_digits("123456789") == "1-9"
assert shorten_digits("456789")    == "4-9"
assert shorten_digits("256789")    == "25-9"
```

### Data Downloads

This script is used to download various inputs stored as `examples/sudoku_*.txt`.

```bash
# exec: bash
set -e
set -o pipefail
if [[ ! -f "examples/sudoku_p096_euler.txt" ]]; then
    curl --silent "https://projecteuler.net/project/resources/p096_sudoku.txt" > "examples/_sudoku_p096_euler.txt"
    awk '{if (!match($0, "Grid")) {line=line$0;if (length(line) == 81) {gsub(0, ".", line);print line;line="";}}}' \
        "examples/_sudoku_p096_euler.txt" \
        > examples/sudoku_p096_euler.txt
    rm examples/_sudoku_p096_euler.txt
fi

if [[ ! -f "examples/sudoku_top95.txt" ]]; then
    curl --silent "http://norvig.com/top95.txt" > "examples/sudoku_top95.txt"
fi

if [[ ! -f "examples/sudoku_hardest.txt" ]]; then
    curl --silent "http://norvig.com/hardest.txt" > "examples/sudoku_hardest.txt"
fi
```


### Statistics Collection/Charts

The `collect_stats.py` script generates the statistics for the two plots of calculation times.

```python
# def: paths
from pathlib import Path

STATIC_DIR = Path("lit_v3") / "static"
TIMES_PATH = Path("examples") / "sudoku_random_times.csv"

LIN_PATH = STATIC_DIR / "sudoku_random_puzzle_times_linear.svg"
LOG_PATH = STATIC_DIR / "sudoku_random_puzzle_times_log.svg"
```

```python
# file: examples/collect_stats.py
# dep: boilerplate, paths, random_puzzle
import os, math, time
from multiprocessing import Pool


def collect_time(*args) -> int:
    while True:
        raw_grid = random_puzzle()
        tzero = time.time()
        solve(raw_grid)
        duration_ms = (time.time() - tzero) * 1000
        if duration_ms > 50:
            return round(duration_ms)


def main():
    tzero = time.time()

    pool_size = max(1, len(os.sched_getaffinity(0)) - 2)
    pool = Pool(pool_size)
    for result in pool.imap_unordered(collect_time, range(pool_size)):
        with TIMES_PATH.open(mode="a") as fobj:
            fobj.write("\n" + str(result))

    print(f"duration: {time.time() - tzero:9.3f} sec")

if __name__ == '__main__':
    main()
```

```bash
# run: python3 examples/collect_stats.py
# def: calc_random_puzzle_times
# timeout: 1000
duration:    98.400 sec
# exit: 0
```

I spent a few hours on different ways to render plots eventually gave up on getting it the way I wanted (as close as possible to the originals). I'm not fond of the matplotlib API...

```python
# exec
# dep: paths, overview.save_bar_plot
# requires: calc_random_puzzle_times
import os, math
import pandas as pd

df = pd.read_csv(str(TIMES_PATH), header=0, names=["ms"])
df = df[df['ms'] > 1000]
df['sec'] = df['ms'] / 1000

STATIC_DIR.mkdir(exist_ok=True)
times = df['sec'].sort_values()
times = times.reset_index(drop=True)

save_bar_plot(times, str(LIN_PATH))
save_bar_plot(times, str(LOG_PATH), logy=True)
```
