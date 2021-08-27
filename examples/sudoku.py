from typing import Optional, Iterator
DIGITS = "123456789"
import re
def parse_grids(text: str) -> Iterator[str]:
    puzzle = ""
    for line in text.splitlines():
        line, _ = re.subn(r"[^0-9\.]",  "", line)
        puzzle += line
        if len(puzzle) == 81:
            yield puzzle
            puzzle = ""
def read_grids(filename: str) -> list[str]:
    with open(filename) as fobj:
        grids_text = fobj.read()
    return list(parse_grids(grids_text))
def cross(A: list[str], B: list[str]) -> list[str]:
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
GridItem  = tuple[Square, Digits]
Grid      = dict[Square, Digits]
MaybeGrid = Optional[Grid]
def grid_items(raw_grid: str) -> Iterator[GridItem]:
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
    """Eliminate all the other values (except d) from grid[s] and propagate.
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
        # propagate initial constraint
        if d.isdigit() and assign(grid, s, d) is None:
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
def display(grid: Grid) -> None:
    """Display compact 2-D representation of grid."""
    # copy to prevent modification of our input
    grid = grid.copy()
    for s in grid:
        digits = grid[s]
        if digits == DIGITS or digits == ".":
            grid[s] = ""
        elif len(digits) > 5:
            grid[s] = shorten_digits(digits)
    # print with alignment
    width = 1 + max(len(d) for d in grid.values())
    dashed_line = "+".join(["-" * (1 + width * 3)] * 3)
    for r in ROWS:
        centered_row_cells = [
            grid[r + c].center(width) + ("| " if c in "36" else "")
            for c in COLS
        ]
        print(" " + "".join(centered_row_cells))
        if r in "CF":
            print(dashed_line)
    print()
import time
def solve_all(raw_grids: list[str], show: bool) -> None:
    durations: list[float] = []
    for raw_grid in raw_grids:
        tzero = time.time()
        result = solve(raw_grid)
        if result:
            durations.append(time.time() - tzero)
        if result and show:
            display(result)
    avg_ms = round((sum(durations) * 1000) / len(durations))
    max_ms = round(max(durations) * 1000)
    print(f"Solved {len(durations)} of {len(raw_grids)} puzzles.", end=" ")
    print(f"(avg {avg_ms} ms/solve  max {max_ms} ms)")
import os
import sys
def main(args: list[str]) -> int:
    show = "--show" in args
    for filename in args:
        if os.path.exists(filename):
            raw_grids = read_grids(filename)
            solve_all(raw_grids, show)
    return 0
if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))