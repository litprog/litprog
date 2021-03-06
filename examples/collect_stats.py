from typing import Sequence, Tuple, List, Dict, Optional, Iterable
DIGITS = "123456789"
from pathlib import Path
STATIC_DIR = Path("lit_v3") / "static"
TIMES_PATH = Path("examples") / "sudoku_random_times.csv"
LIN_PATH = STATIC_DIR / "sudoku_random_puzzle_times_linear.svg"
LOG_PATH = STATIC_DIR / "sudoku_random_puzzle_times_log.svg"
def cross(A: Sequence[str], B: Sequence[str]) -> Sequence[str]:
    """Cross product of elements in A and elements in B."""
    return [a + b for a in A for b in B]
ROWS    = list("ABCDEFGHI")
COLS    = list("123456789")
SQUARES = cross(ROWS, COLS)
assert len(SQUARES) == 81
UNITLIST = (
    [cross(ROWS, c) for c in COLS]
    + [cross(r, COLS) for r in ROWS]
    + [
        cross(rs, cs)
        for rs in ('ABC', 'DEF', 'GHI')
        for cs in ('123', '456', '789')
    ]
)
UNITS = {
    s: [u for u in UNITLIST if s in u]
    for s in SQUARES
}
PEERS = {
    s: set(sum(UNITS[s], [])) - {s}
    for s in SQUARES
}
Square = str
Digits = str     # length >= 1
Digit  = str     # length == 1
GridItem  = Tuple[Square, Digits]
Grid      = Dict[Square, Digits]
MaybeGrid = Optional[Grid]
def grid_items(raw_grid: str) -> Iterable[GridItem]:
    """Parse string representation of a Grid with '.' for empties."""
    chars = [c for c in raw_grid if c.isdigit() or c == '.']
    assert len(chars) == len(SQUARES)
    return zip(SQUARES, chars)
def eliminate(grid: Grid, s: Square, d: Digit) -> MaybeGrid:
    """Eliminate d from grid[s];
    propagate when grid or places <= 2.
    return `None` if a contradiction is detected.
    """
    if d not in grid[s]:
        return grid   # Already eliminated
    grid[s] = grid[s].replace(d, '')
    if len(grid[s]) == 0:
        return None   # Contradiction: removed last value
    # (1) If a square s is reduced to one value d2,
    #   then propagate elimination of d2 to its peers.
    if len(grid[s]) == 1:
        d2 = grid[s]
        if not all(eliminate(grid, s2, d2) for s2 in PEERS[s]):
            return None
    # (2) If a unit u is reduced to only one place for a value d,
    #   then put it there.
    for u in UNITS[s]:
        squares = [s for s in u if d in grid[s]]
        if len(squares) == 0:
            return None  # Contradiction: no place for this value
        elif len(squares) == 1:
            # d can only be in one place in unit; assign it there
            if assign(grid, squares[0], d) is None:
                return None
    return grid
def assign(grid: Grid, s: Square, d: Digit) -> MaybeGrid:
    """Eliminate all the other grid (except d) from grid[s] and propagate.
    if a contradiction is detected, return None
    """
    others = grid[s].replace(d, "")
    for d in others:
        if eliminate(grid, s, d) is None:
            return None
    return grid
def parse_grid(raw_grid: str) -> MaybeGrid:
    """Convert grid to a dict of possible values.
    return None if a contradiction is detected.
    """
    # To start, every square can be any digit;
    # then assign values from the grid.
    grid = {s: DIGITS for s in SQUARES}
    for s, d in grid_items(raw_grid):
        if not d.isdigit():
            continue
        # propagate initial constraint
        if assign(grid, s, d) is None:
            return None
    return grid
def search(grid: Grid) -> MaybeGrid:
    """Using depth-first search and propagation, try all possible values."""
    if grid is None:
        return None     # Failed earlier
    elif all(len(v) == 1 for v in grid.values()):
        return grid     # Solved!
    else:
        # Chose the unfilled square s with the fewest possibilities
        _, s = min((len(v), s) for s, v in grid.items() if len(v) > 1)
        for d in grid[s]:
            solution = search(assign(grid.copy(), s, d))
            if solution:
                return solution
        return None
def solve(raw_grid: str) -> MaybeGrid:
    return search(parse_grid(raw_grid))
import random
def shuffled(seq: Sequence[str]) -> Sequence[str]:
    "Return a randomly shuffled copy of the input sequence."
    seq = list(seq)
    random.shuffle(seq)
    return seq
def random_puzzle(n=17) -> str:
    """Make a random puzzle with n or more assignments.
    Restart on contradictions.
    Note the resulting puzzle is not guaranteed to be solvable, but empirically
    about 99.8% of them are solvable. Some have multiple solutions.
    """
    grid: Grid = {s: DIGITS for s in SQUARES}
    for s in shuffled(SQUARES):
        if assign(grid, s, random.choice(grid[s])) is None:
            return random_puzzle(n)    # Give up and make a new puzzle
        else:
            ds = [grid[s] for s in SQUARES if len(grid[s]) == 1]
            if len(ds) >= n and len(set(ds)) >= 8:
                return ''.join(
                    grid[s] if len(grid[s]) == 1 else '.'
                    for s in SQUARES
                )
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