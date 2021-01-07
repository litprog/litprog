# Solve Every Sudoku Puzzle

Where the previous chapter *described* how LitProg works, this chapter aims to *demonstrate* by example how LitProg can be used.

This chapter produces the following artifacts:

|            filename            |              description              |
|--------------------------------|---------------------------------------|
| examples/sudoku.py             | A cli program to solve sudoku puzzles |
| examples/sudoku_p096_euler.txt | 50 problems from projecteuler.net     |
| examples/sudoku_top95.txt      | 95 hard puzzles                       |
| examples/sudoku_hardest.txt    | 11 hard puzzles                       |
| examples/sudoku_hardester.txt  | 2 hardest puzzels by Arto Inkala      |


## Introduction

> This chapter is a recasting of the essay [Solving Every Sudoku Puzzle by Peter Norvig](http://norvig.com/sudoku.html).

It is quite easy to solve every Sudoku puzzle with two ideas: [constraint propagation](http://en.wikipedia.org/wiki/Constraint_satisfaction) and [search](http://en.wikipedia.org/wiki/Search_algorithm).


## Sudoku Notation and Preliminary Notions

First we have to agree on some notation. A Sudoku puzzle is a *grid* of 81 squares; the majority of enthusiasts label the columns `1-9`, the rows `A-I` (in other words, exactly as Excel would **NOT** label them). Here are the names of the squares:

```
        1  2  3    4  5  6    7  8  9
    A  A1 A2 A3 | A4 A5 A6 | A7 A8 A9
    B  B1 B2 B3 | B4 B5 B6 | B7 B8 B9
    C  C1 C2 C3 | C4 C5 C6 | C7 C8 C9
      ----------+----------+----------
    D  D1 D2 D3 | D4 D5 D6 | D7 D8 D9
    E  E1 E2 E3 | E4 E5 E6 | E7 E8 E9
    F  F1 F2 F3 | F4 F5 F6 | F7 F8 F9
      ----------+----------+----------
    G  G1 G2 G3 | G4 G5 G6 | G7 G8 G9
    H  H1 H2 H3 | H4 H5 H6 | H7 H8 H9
    I  I1 I2 I3 | I4 I5 I6 | I7 I8 I9
```

A collection of nine squares (column, row, or box) we call a *unit* and the squares that share a unit we call *peers* of each other. Every square has exactly 3 units and 20 peers. For example, here are the units and peers for the square C2:

```
        1 2 3   4 5 6   7 8 9
    A   o o o |       |
    B   o o o |       |
    C   o X o | o o o | o o o
       -------+-------+-------
    D     o   |       |
    E     o   |       |
    F     o   |       |
       -------+-------+-------
    G     o   |       |
    H     o   |       |
    I     o   |       |
```

A puzzle leaves some squares blank and fills others with digits, and the whole idea is this:

> **A puzzle is solved if the squares in each unit are filled with a permutation of the digits 1 to 9.**

That is, no digit can appear twice in a unit, and every digit must appear once. This implies that each square must have a different value from any of its peers. Here is a typical puzzle, and its solution.

```
  1 2 3   4 5 6   7 8 9      1 2 3   4 5 6   7 8 9
A 4 . . | . . . | 8 . 5    A 4 1 7 | 3 6 9 | 8 2 5
B . 3 . | . . . | . . .    B 6 3 2 | 1 5 8 | 9 4 7
C . . . | 7 . . | . . .    C 9 5 8 | 7 2 4 | 3 1 6
  ------+-------+------      ------+-------+------
D . 2 . | . . . | . 6 .    D 8 2 5 | 4 3 7 | 1 6 9
E . . . | . 8 . | 4 . .    E 7 9 1 | 5 8 6 | 4 3 2
F . . . | . 1 . | . . .    F 3 4 6 | 9 1 2 | 7 5 8
  ------+-------+------      ------+-------+------
G . . . | 6 . 3 | . 7 .    G 2 8 9 | 6 4 3 | 5 7 1
H 5 . . | 2 . . | . . .    H 5 7 3 | 2 9 1 | 6 8 4
```

We can implement the notions of units, peers, and squares in Python 3.6+ as follows:

```python
# lp_def: notions
# lp_dep: boilerplate

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
```

```python
# lp_exec
# lp_dep: notions
assert len(UNITLIST) == 27
assert all(len(UNITS[s]) == 3 for s in SQUARES)
assert all(len(PEERS[s]) == 20 for s in SQUARES)
assert UNITS['C2'] == [
    ['A2', 'B2', 'C2', 'D2', 'E2', 'F2', 'G2', 'H2', 'I2'],
    ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9'],
    ['A1', 'A2', 'A3', 'B1', 'B2', 'B3', 'C1', 'C2', 'C3'],
]
assert PEERS['C2'] == {
    'A2', 'B2', 'D2', 'E2', 'F2', 'G2', 'H2', 'I2',
    'C1', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9',
    'A1', 'A2', 'A3', 'B1', 'B2', 'B3', 'C1', 'C3',
}
assert 'C2' not in PEERS['C2']
```

Now that we have squares, units, and peers, the next step is to define the Sudoku grid. Actually we need two representations:

1. A textual format used to specify the initial state of a puzzle; we will reserve the name *grid* for this.
2. An internal representation of any state of a puzzle, partially solved or complete; this we will call a *values* collection because it will give all the remaining possible values for each square.

For the textual format we'll allow a string of characters with 1-9 to indicate a digit, and a period to specify an empty square. All other characters are ignored (including spaces, newlines, dashes, and bars). So each of the following three grid strings represent the same puzzle:

```python
# lp_def: fixtures
FIXTURE_1 = """
  4.....8.5.3..........7.....
  .2.....6.....8.4......1....
  ...6.3.7.5..2.....1.4......
"""

FIXTURE_2 = """
  4.....8.5
  .3.......
  ...7.....
  .2.....6.
  ....8.4..
  ....1....
  ...6.3.7.
  5..2.....
  1.4......
"""

FIXTURE_3 = """
4 . . |. . . |8 . 5
. 3 . |. . . |. . .
. . . |7 . . |. . .
------+------+------
. 2 . |. . . |. 6 .
. . . |. 8 . |4 . .
. . . |. 1 . |. . .
------+------+------
. . . |6 . 3 |. 7 .
5 . . |2 . . |. . .
1 . 4 |. . . |. . .
"""
```

Now for *values*. One might think that a 9 x 9 array would be the obvious data structure. But squares have names like `'A1'`, not `(0,0)`. Therefore, *values* will be a `dict` with squares as keys. The value for each key will be the possible digits for that square: a single digit if it was given as part of the puzzle definition or if we have figured out what it must be. If we are still uncertain of a value, a collection of several digits is assigned to the square. This collection of digits could be represented by a Python `set` or `list`, but I chose instead to use a string of digits (we'll see why later). So a grid where A1 is 7 and C7 is empty would be represented as `{'A1': '7', 'C7': '123456789', ...}`.

Here is the code to parse a grid into a values dict:

```python
# lp_def: grid_items
# lp_dep: notions

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
```

```python
# lp_exec
# lp_dep: grid_items, fixtures
assert dict(grid_items(FIXTURE_1)) == dict(grid_items(FIXTURE_2))
assert dict(grid_items(FIXTURE_1)) == dict(grid_items(FIXTURE_3))
```


## Grid Display

Soon enough we'll want to see our partial results, so we'll need a function to `display` a puzzle.

```python
# lp_def: display
# lp_dep: shorten_digits
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
```

```python
# lp_exec: python3
# lp_dep: fixtures, grid_items, display
display(dict(grid_items(FIXTURE_1)))
```

```python
# lp_out
 4     |       | 8   5
   3   |       |
       | 7     |
-------+-------+-------
   2   |       |   6
       |   8   | 4
       |   1   |
-------+-------+-------
       | 6   3 |   7
 5     | 2     |
 1   4 |       |
# exit: 0
```


## Constraint Propagation

Those with experience solving Sudoku puzzles know that there are two important strategies that we can use to make progress towards a solution:

1. If a square has only one possible value, then eliminate that value from the peers of the square.
2. If a unit has only one possible place for a value, then put the value there.

As an example of strategy 1: If we assign 7 to `A1`, yielding `{'A1': '7', 'A2':'123456789', ...}`, we see that `A1` has only one value, and thus the 7 can be removed from its peer `A2` (and all other peers), giving us `{'A1': '7', 'A2': '12345689', ...}`.

As an example of strategy 2: If it turns out that none of `A3` through `A9` has a 3 as a possible value, then the 3 must belong in `A2`, and we can update to `{'A1': '7', 'A2':'3', ...}`. These updates to `A2` may in turn cause further updates to its peers, and the peers of those peers, and so on. This process is called *constraint propagation*.

The function `assign` will return the updated values (including the updates from constraint propagation), but if there is a contradiction (if the assignment cannot be made consistently) then `assign` returns `None`. For example, if a grid starts with the digits `'77...'` then when we try to assign the 7 to `A2`, assign would notice that 7 is not a possibility for `A2`, because it was eliminated by the peer, `A1`.

It turns out that the fundamental operation is not assigning a value, but rather eliminating one of the possible values for a square, which we implement with the `eliminate` function.

```python
# lp_def: eliminate
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
```

We could implement `assign` as `grid[s] = d`, but we can do more than just that. Once we have `eliminate`, then `assign` can be defined as "eliminate all the digits at `s` except `d`". This approach triggers the recursive constraint propagation.

```python
# lp_def: assign
# lp_dep: eliminate
def assign(grid: Grid, s: Square, d: Digit) -> MaybeGrid:
    """Eliminate all the other grid (except d) from grid[s] and propagate.

    if a contradiction is detected, return None
    """
    others = grid[s].replace(d, "")
    for d in others:
        if eliminate(grid, s, d) is None:
            return None
    return grid
```

Now we can proceed to actually use our building blocks and solve a puzzle. The function `parse_grid` calls `assign`, which in turn will call `elimitate`...

```python
# lp_def: parse_grid
# lp_dep: grid_items, assign
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
```

Now we're ready to go. I picked the first example from a list of [easy puzzles](http://norvig.com/easy50.txt) from the fine [Project Euler](http://projecteuler.net/) [Sudoku problem](http://projecteuler.net/index.php?section=problems&id=96) and tried it:

```python
# lp_exec
# lp_dep: parse_grid, display
grid1 = """
..3.2.6..9..3.5..1..18.64..
..81.29..7.......8..67.82..
..26.95..8..2.3..9..5.1.3..
"""

display(parse_grid(grid1))
```

```python
# lp_out
 4 8 3 | 9 2 1 | 6 5 7
 9 6 7 | 3 4 5 | 8 2 1
 2 5 1 | 8 7 6 | 4 9 3
-------+-------+-------
 5 4 8 | 1 3 2 | 9 7 6
 7 2 9 | 5 6 4 | 1 3 8
 1 3 6 | 7 9 8 | 2 4 5
-------+-------+-------
 3 7 2 | 6 8 9 | 5 1 4
 8 1 4 | 2 5 3 | 7 6 9
 6 9 5 | 4 1 7 | 3 8 2
# exit: 0
```

In this case, the puzzle was completely solved by rote application of strategies 1. and 2.! Unfortunately, that will not always be the case. Here is the first example from a list of [hard puzzles](http://magictour.free.fr/top95):

```python
# lp_def: grid2
grid2 = """
4.....8.5.3..........7.....
.2.....6.....8.4......1....
...6.3.7.5..2.....1.4......
"""
```

```python
# lp_exec
# lp_dep: parse_grid, display, grid2
display(parse_grid(grid2))
```

```python
# lp_out
    4     1679  12679 |   139    2369   269  |    8     1239    5
  26789    3    125-9 |  14589  24569  245689|  12679   1249  124679
   2689  15689  125689|    7     2-69  245689|  12369  12349  1-469
----------------------+----------------------+----------------------
   3789    2    15789 |   3459  34579   4579 |  13579    6    13789
   3679  15679  15679 |   359     8    25679 |    4    12359  12379
  36789    4    56789 |   359     1    25679 |  23579  23589  23789
----------------------+----------------------+----------------------
   289     89    289  |    6     459     3   |   1259    7    12489
    5     6789    3   |    2     479     1   |    69    489    4689
    1     6789    4   |   589    579    5789 |  23569  23589  23689
# exit: 0
```

In this case, we are still a long way from solving the puzzle--61 squares remain uncertain. What next? We could try to code [more sophisticated strategies](http://www.sudokudragon.com/sudokustrategy.htm). For example, the *naked twins* strategy looks for two squares in the same unit that both have the same two possible digits. Given `{'A5': '26', 'A6':'26', ...}`, we can conclude that 2 and 6 must be in `A5` and `A6` (although we don't know which is where), and we can therefore eliminate 2 and 6 from every other square in the `A` row unit. We could code that strategy in a few lines by adding an `elif len(values[s]) == 2` test to `eliminate`.

Coding up strategies like this is a possible route, but would require hundreds of lines of code (there are dozens of these strategies), and we'd never be sure if we could solve *every* puzzle.

## Search

The other route is to *search* for a solution: to systematically try all possibilities until we hit one that works. The code for this is less than a dozen lines, but we run another risk: that it might take forever to run. Consider that in the `grid2` above, `A2` has 4 possibilities (`1679`) and `A3` has 5 possibilities (`12679`); together that's 20, and if we keep [multiplying](http://www.google.com/search?hl=en&q=4*5*3*4*3*4*5*7*5*5*6*5*4*6*4*5*6*6*6*5*5*6*4*5*4*5*4*5*5*4*5*5*3*5*5*5*5*5*3*5*5*5*5*3*2*3*3*4*5*4*3*2*3*4*4*3*3*4*5*5*5), we get $`4.62838344192 × 10^{38}`$ possibilities for the whole puzzle. How can we cope with that? There are two choices.

First, we could try a brute force approach. Suppose we have a very efficient program that takes only one instruction to evaluate a position, and that we have access to the next-generation computing technology, let's say a 10GHz processor with 1024 cores, and let's say we could afford a million of them, and while we're shopping, let's say we also pick up a time machine and go back 13 billion years to the origin of the universe and start our program running. We can then [compute](http://www.google.com/search?&q=10+GHz+*+1024+*+1+million+*+13+billion+years+%2F+4.6e38+in+percent) that we'd be almost 1% done with this one puzzle by now.

The second choice is to somehow process much more than one possibility per machine instruction. That seems impossible, but fortunately it is exactly what constraint propagation does for us. We don't have to try all $`4 × 10^{38}`$ possibilities because as soon as we try one we immediately eliminate many other possibilities. For example, square H7 of this puzzle has two possibilities, 6 and 9\. We can try 9 and quickly see that there is a contradiction. That means we've eliminated not just one possibility, but fully _half_ of the $`4 × 10^{38}`$ choices.

In fact, it turns out that to solve this particular puzzle we need to look at only 25 possibilities and we only have to explicitly search through 9 of the 61 unfilled squares; constraint propagation does the rest. For the list of 95 [hard puzzles](http://magictour.free.fr/top95), on average we need to consider 64 possibilities per puzzle, and in no case do we have to search more than 16 squares.

What is the search algorithm? Simple: first make sure we haven't already found a solution or a contradiction, and if not, choose one unfilled square and consider all its possible values. One at a time, try assigning the square each value, and searching from the resulting position. In other words, we search for a value `d` such that we can successfully search for a solution from the result of assigning square `s` to `d`. If the search leads to an failed position, go back and consider another value of `d`. This is a *recursive* search, and we call it a *[depth-first](http://en.wikipedia.org/wiki/Depth-first_search)* search because we (recursively) consider all possibilities under `values[s] = d` before we consider a different value for `s`.

To avoid bookkeeping complications, we create a new copy of `values` for each recursive call to `search`. This way each branch of the search tree is independent, and doesn't confuse another branch. (This is why I chose to implement the set of possible values for a square as a string: I can copy `values` with `values.copy()` which is simple and efficient. If I implemented a possibility as a Python `set` or `list` I would need to use `copy.deepcopy(values)`, which is less efficient.) The alternative is to keep track of each change to `values` and undo the change when we hit a dead end. This is known as *[backtracking search](http://en.wikipedia.org/wiki/Backtracking_search)*. It makes sense when each step in the search is a single change to a large data structure, but is complicated when each assignment can lead to many other changes via constraint propagation.

There are two choices we have to make in implementing the search: *variable ordering* (which square do we try first?) and *value ordering* (which digit do we try first for the square?). For variable ordering, we will use a common heuristic called *minimum remaining values*, which means that we choose the (or one of the) square with the minimum number of possible values. Why? Consider `grid2` above. Suppose we chose `B3` first. It has 7 possibilities (`1256789`), so we'd expect to guess wrong with probability $`6/7`$. If instead we chose `G2`, which only has 2 possibilities (`89`), we'd expect to be wrong with probability only $`1/2`$. Thus we choose the square with the fewest possibilities and the best chance of guessing right. For value ordering we won't do anything special; we'll consider the digits in numeric order.

Now we're ready to define the `solve` function in terms of the `search` function:

```python
# lp_def: solve
# lp_dep: parse_grid
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
```

**That's it!** We're done; it only took one page of code, and we can now solve any Sudoku puzzle, including `grid2` which we previously couldn't.

```python
# lp_exec
# lp_dep: solve, display, grid2
display(solve(grid2))
```

```python
# lp_out
 4 1 7 | 3 6 9 | 8 2 5
 6 3 2 | 1 5 8 | 9 4 7
 9 5 8 | 7 2 4 | 3 1 6
-------+-------+-------
 8 2 5 | 4 3 7 | 1 6 9
 7 9 1 | 5 8 6 | 4 3 2
 3 4 6 | 9 1 2 | 7 5 8
-------+-------+-------
 2 8 9 | 6 4 3 | 5 7 1
 5 7 3 | 2 9 1 | 6 8 4
 1 6 4 | 8 7 5 | 2 9 3
# exit: 0
```

## CLI Program

Now we can create the complete program `examples/sudoku.py`.

```python
# lp_def: read_grids
# lp_dep: boilerplate
import re

def parse_grids(text: str) -> Iterable[str]:
    puzzle = ""
    for line in text.splitlines():
        line, _ = re.subn(r"[^0-9\.]",  "", line)
        puzzle += line
        if len(puzzle) == 81:
            yield puzzle
            puzzle = ""

def read_grids(filename: str) -> List[str]:
    with open(filename) as fobj:
        grids_text = fobj.read()
    return list(parse_grids(grids_text))
```

```python
# lp_def: solve_all
# lp_dep: boilerplate, solve, display
import time

def solve_all(raw_grids: List[str], show: bool) -> None:
    durations: List[float] = []
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
```

```python
# lp_file: examples/sudoku.py
# lp_dep: read_grids, solve_all
import os
import sys

def main(args: Sequence[str]) -> int:
    show = "--show" in args
    for filename in args:
        if os.path.exists(filename):
            raw_grids = read_grids(filename)
            solve_all(raw_grids, show)
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
```

```bash
# lp_exec
isort examples/sudoku.py
sjfmt examples/sudoku.py
```


## Results

Below is the output from running the program at the command line; it solves the two files of [50 easy](http://projecteuler.net/project/sudoku.txt) and [95 hard puzzles](http://norvig.com/top95.txt) (see also the [95 solutions](http://norvig.com/top95solutions.html), [eleven puzzles](http://norvig.com/hardest.txt) I found under a search for ( [hardest sudoku](http://www.google.com/search?q=hardest+sudoku) ).

```bash
# lp_run: python examples/sudoku.py examples/sudoku_p096_euler.txt
Solved 50 of 50 puzzles. (avg 2 ms/solve  max 3 ms)
# exit: 0
```

```bash
# lp_run: python examples/sudoku.py examples/sudoku_top95.txt
Solved 95 of 95 puzzles. (avg 8 ms/solve  max 38 ms)
# exit: 0
```

```bash
# lp_run: python examples/sudoku.py examples/sudoku_hardest.txt
Solved 11 of 11 puzzles. (avg 3 ms/solve  max 6 ms)
# exit: 0
```


## Analysis

!!! note "Execution Timeings from 2006 vs 2020"

    The original essay by Peter Norvig was written in 2006. This section uses
    some of the execution times from that essay, but the plots were generated based on execution times from a newer machine.

Each of the puzzles above was solved in less than a fifth of a second. What about really hard puzzles? Finnish mathematician Arto Inkala described his [2006 puzzle](http://www.usatoday.com/news/offbeat/2006-11-06-sudoku_x.htm) as "the most difficult sudoku-puzzle known so far" and his [2010 puzzle](http://www.mirror.co.uk/fun-games/sudoku/2010/08/19/world-s-hardest-sudoku-can-you-solve-dr-arto-inkala-s-puzzle-115875-22496946/) as "the most difficult puzzle I've ever created." My program solves them in 0.01 seconds each:

```bash
# lp_file: examples/sudoku_hardester.txt
8 5 . |. . 2 |4 . .
7 2 . |. . . |. . 9
. . 4 |. . . |. . .
------+------+------
. . . |1 . 7 |. . 2
3 . 5 |. . . |9 . .
. 4 . |. . . |. . .
------+------+------
. . . |. 8 . |. 7 .
. 1 7 |. . . |. . .
. . . |. 3 6 |. 4 .

. . 5 |3 . . |. . .
8 . . |. . . |. 2 .
. 7 . |. 1 . |5 . .
------+------+------
4 . . |. . 5 |3 . .
. 1 . |. 7 . |. . 6
. . 3 |2 . . |. 8 .
------+------+------
. 6 . |5 . . |. . 9
. . 4 |. . . |. 3 .
. . . |. . 9 |7 . .
```

```python
# lp_run: python examples/sudoku.py --show examples/sudoku_hardester.txt
 8 5 9 | 6 1 2 | 4 3 7
 7 2 3 | 8 5 4 | 1 6 9
 1 6 4 | 3 7 9 | 5 2 8
-------+-------+-------
 9 8 6 | 1 4 7 | 3 5 2
 3 7 5 | 2 6 8 | 9 1 4
 2 4 1 | 5 9 3 | 7 8 6
-------+-------+-------
 4 3 2 | 9 8 1 | 6 7 5
 6 1 7 | 4 2 5 | 8 9 3
 5 9 8 | 7 3 6 | 2 4 1

 1 4 5 | 3 2 7 | 6 9 8
 8 3 9 | 6 5 4 | 1 2 7
 6 7 2 | 9 1 8 | 5 4 3
-------+-------+-------
 4 9 6 | 1 8 5 | 3 7 2
 2 1 8 | 4 7 3 | 9 5 6
 7 5 3 | 2 9 6 | 4 8 1
-------+-------+-------
 3 6 7 | 5 4 2 | 8 1 9
 9 8 4 | 7 6 1 | 2 3 5
 5 2 1 | 8 3 9 | 7 6 4

Solved 2 of 2 puzzles. (avg 4 ms/solve  max 4 ms)
# exit: 0
```

I guess if I want a really hard puzzle I'll have to make it myself. I don't know how to make hard puzzles, so I generated a million random puzzles. My algorithm for making a random puzzle is simple: first, randomly shuffle the order of the squares. One by one, fill in each square with a random digit, respecting the possible digit choices. If a contradiction is reached, start over. If we fill at least 17 squares with at least 8 different digits then we are done. (Note: with less than 17 squares filled in or less than 8 different digits it is known that there will be duplicate solutions. Thanks to Olivier Grégoire for the fine suggestion about 8 different digits.)

```python
# lp_def: random_puzzle
# lp_dep: boilerplate, solve
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
```

Even with these checks, my random puzzles are not guaranteed to have one unique solution. Many have multiple solutions, and a few (about 0.2%) have no solution. Puzzles that appear in books and newspapers always have one unique solution.

The average time to solve a random puzzle is 0.01 seconds, and more than 99.95% took less than 0.1 seconds, but a few took much longer:

- `0.032%      (1 in 3,000) took more than 0.1 seconds`
- `0.014%      (1 in 7,000) took more than 1 second`
- `0.003%     (1 in 30,000) took more than 10 seconds`
- `0.0001% (1 in 1,000,000) took more than 100 seconds`

Here are the times in seconds for the 139 out of a million puzzles that took more than a second, sorted, on linear and log scales:

![](static/sudoku_random_puzzle_times_linear.svg)
![](static/sudoku_random_puzzle_times_log.svg)

It is hard to draw conclusions from this. Is the uptick in the last few values significant? If I generated 10 million puzzles, would one take 1000 seconds? Here's the hardest (for my program) of the million random puzzles:

```shell
# lp_file: examples/sudoku_hardestest.txt
 . . . | . . 6 | . . .
 . 5 9 | . . . | . . 8
 2 . . | . . 8 | . . .
-------+-------+-------
 . 4 5 | . . . | . . .
 . . 3 | . . . | . . .
 . . 6 | . . 3 | . 5 4
-------+-------+-------
 . . . | 3 2 5 | . . 6
 . . . | . . . | . . .
 . . . | . . . | . . .
```

I capture the result in `examples/sudoku_hardestest_result.txt`, just so I don't have to recompute it again and again during development.

```shell
# lp_exec
# lp_timeout: 60
if [[ ! -f examples/sudoku_hardestest_result.txt ]]; then
    python examples/sudoku.py \
        --show examples/sudoku_hardestest.txt \
        > examples/sudoku_hardestest_result.txt
fi
```

```shell
# lp_run: cat examples/sudoku_hardestest_result.txt
 4 3 8 | 7 9 6 | 2 1 5
 6 5 9 | 1 3 2 | 4 7 8
 2 7 1 | 4 5 8 | 6 9 3
-------+-------+-------
 8 4 5 | 2 1 9 | 3 6 7
 7 1 3 | 5 6 4 | 8 2 9
 9 2 6 | 8 7 3 | 1 5 4
-------+-------+-------
 1 9 4 | 3 2 5 | 7 8 6
 3 6 2 | 9 8 7 | 5 4 1
 5 8 7 | 6 4 1 | 9 3 2

Solved 1 of 1 puzzles. (avg 37519 ms/solve  max 37519 ms)
# exit: 0
```

Unfortunately, this is not a true Sudoku puzzle because it has multiple solutions. (It was generated before I incorporated Olivier Grégoire's suggestion about checking for 8 digits, so note that any solution to this puzzle leads to another solution where the 1s and 7s are swapped.) But is this an intrinsicly hard puzzle? Or is the difficulty an artifact of the particular variable- and value-ordering scheme used by my `search` routine? To test I randomized the value ordering (I changed `for d in values[s]` in the last line of `search` to be `for d in shuffled(values[s])` and implemented `shuffled` using `random.shuffle`). The results were starkly bimodal: in 27 out of 30 trials the puzzle took less than 0.02 seconds, while each of the other 3 trials took just about 190 seconds (about 10,000 times longer). There are multiple solutions to this puzzle, and the randomized `search` found 13 different solutions. My guess is that somewhere early in the search there is a sequence of squares (probably two) such that if we choose the exact wrong combination of values to fill the squares, it takes about 190 seconds to discover that there is a contradiction. But if we make any other choice, we very quickly either find a solution or find a contradiction and move on to another choice. So the speed of the algorithm is determined by whether it can avoid the deadly combination of value choices.

Randomization works most of the time (27 out of 30), but perhaps we could do even better by considering a better value ordering (one popular heuristic is _least-constraining value_, which chooses first the value that imposes the fewest constraints on peers), or by trying a smarter variable ordering.

More experimentation would be needed before I could give a good characterization of the hard puzzles. I decided to experiment on another million random puzzles, this time keeping statistics on the mean, 50th (median), 90th and 99th percentiles, maximum and standard deviation of run times. The results were similar, except this time I got two puzzles that took over 100 seconds, and one took quite a bit longer: 1439 seconds. It turns out this puzzle is one of the 0.2% that has no solution, so maybe it doesn't count. But the main message is that the mean and median stay about the same even as we sample more, but the maximum keeps going up--dramatically. The standard deviation edges up too, but mostly because of the very few very long times that are way out beyond the 99th percentile. This is a _heavy-tailed_ distribution, not a normal one.

For comparison, the tables below give the statistics for puzzle-solving run times on the left, and for samples from a normal (Gaussian) distribution with mean 0.014 and standard deviation 1.4794 on the right. Note that with a million samples, the max of the Gaussian is 5 standard deviations above the mean (roughly what you'd expect from a Gaussian), while the maximum puzzle run time is 1000 standard deviations above the mean.

**Samples of Puzzle Run Time**

|     N     |  mean | 50%  | 90%  | 99%  |   max   | std. dev |
|-----------|-------|------|------|------|---------|----------|
| 10        | 0.012 | 0.01 | 0.01 | 0.01 |    0.02 |   0.0034 |
| 100       | 0.011 | 0.01 | 0.01 | 0.02 |    0.02 |   0.0029 |
| 1,000     | 0.011 | 0.01 | 0.01 | 0.02 |    0.02 |   0.0025 |
| 10,000    | 0.011 | 0.01 | 0.01 | 0.02 |    0.68 |   0.0093 |
| 100,000   | 0.012 | 0.01 | 0.01 | 0.02 |   29.07 |   0.1336 |
| 1,000,000 | 0.014 | 0.01 | 0.01 | 0.02 | 1439.81 |   1.4794 |


**Samples of N(0.014, 1.4794)**

|     N     |  mean | 50%  | 90%  | 99%  | max  | std. dev |
|-----------|-------|------|------|------|------|----------|
| 10        | 0.312 | 1.24 | 1.62 | 1.62 | 1.62 |   1.4061 |
| 100       | 0.278 | 0.18 | 2.33 | 4.15 | 4.15 |   1.4985 |
| 1,000     | 0.072 | 0.10 | 1.94 | 3.38 | 6.18 |   1.4973 |
| 10,000    | 0.025 | 0.05 | 1.94 | 3.45 | 6.18 |   1.4983 |
| 100,000   | 0.017 | 0.02 | 1.91 | 3.47 | 7.07 |   1.4820 |
| 1,000,000 | 0.014 | 0.01 | 1.91 | 3.46 | 7.80 |   1.4802 |

Here is the impossible puzzle that took 1439 seconds:

```
. . . |. . 5 |. 8 .
. . . |6 . 1 |. 4 3
. . . |. . . |. . .
------+------+------
. 1 . |5 . . |. . .
. . . |1 . 6 |. . .
3 . . |. . . |. . 5
------+------+------
5 3 . |. . . |. 6 1
. . . |. . . |. . 4
. . . |. . . |. . .
```

## Why?

Why did I do this? As computer security expert [Ben Laurie](http://en.wikipedia.org/wiki/Ben_Laurie) has stated, Sudoku is "a denial of service attack on human intellect". Several people I know (including my wife) were infected by the virus, and I thought maybe this would demonstrate that they didn't need to spend any more time on Sudoku. It didn't work for my friends (although my wife has since independently kicked the habit without my help), but at least one stranger wrote and said this page worked for him, so I've made the world more productive. And perhaps along the way I've taught something about Python, constraint propagation, and search.


## Appendix

### Boilerplate

```python
# lp_def: boilerplate
from typing import Sequence, Tuple, List, Dict, Optional, Iterable

DIGITS = "123456789"
```

Test case for `grid_items`.

```python
# lp_exec: python3
# lp_dep: grid_items, fixtures
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

The `shorten_digits` function is just to make the output of the `display` funciton a bit less verbose for partially solved puzzles. It's primary use is during debugging/develpment.

### Pretty Printing

```python
# lp_def: shorten_digits
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
# lp_exec: python3
# lp_dep: shorten_digits
assert shorten_digits("12345")     == "1-5"
assert shorten_digits("123456789") == "1-9"
assert shorten_digits("456789")    == "4-9"
assert shorten_digits("256789")    == "25-9"
```

### Data Downloads

This script is used to download various inputs stored as `examples/sudoku_*.txt`.

```bash
# lp_exec: bash
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

This script generates the statistics for the two plots of calculation times.

```python
# lp_def: calc_random_puzzle_times
# lp_dep: random_puzzle
import math, time, collections

def round_to_2(x):
    return int(round(x, - int(math.log10(abs(x)) - 1)))

times = collections.Counter()

for _ in range(100):
    raw_grid = random_puzzle()
    tzero = time.time()
    solve(raw_grid)
    duration_ms = (time.time() - tzero) * 1000
    times[round_to_2(duration_ms)] += 1
```

Update the persisted/serialized data, which is kept on disk, since it is expensive to calculate and we don't want to slow down `litprog build`, esp. with `--in-place-update`.

```python
# lp_exec
# lp_dep: calc_random_puzzle_times
import pathlib

DATA_PATH = pathlib.Path("examples/sudoku_random_times.csv")

if DATA_PATH.exists():
    with DATA_PATH.open(mode="r") as in_fobj:
        for line in in_fobj:
            k, v = line.split(",")
            times[int(k)] += int(v)

times_data = "".join(f"{k},{v}\n" for k, v in sorted(times.items()))

with DATA_PATH.open(mode="w") as out_fobj:
    out_fobj.write(times_data)
```

I spent a few hours on different ways to render plots eventually gave up on getting it the way I wanted (as close as possible to the originals). The matplotlib API is a travasty.

```python
# lp_exec
import os, math
import pandas

df = pandas.read_csv(
    "examples/sudoku_random_times.csv",
    header=0,
    names=["ms", "count"],
)
df = df[df.ms > 1000]
df['sec'] = df['ms'] / 1000
df['sec_log'] = df['sec'].apply(math.log)

os.makedirs("lit_v3/static/", exist_ok=True)

def save_bar_plot(series, path: str, **kwargs) -> None:
    # I am aware that this is manipulates global state
    # and I don't like it either. I can't be bothered
    # to deal with this anymore.
    plot = series.plot.bar(legend=None, colormap="gray", **kwargs)
    plot.axes.xaxis.set_visible(False)
    plot.figure.set_size_inches((3.5 * 1.78, 3.5))
    plot.figure.savefig(path, transparent=True)

save_bar_plot(
    df['sec'],
    "lit_v3/static/sudoku_random_puzzle_times_linear.svg",
)
save_bar_plot(
    df['sec_log'],
    "lit_v3/static/sudoku_random_puzzle_times_log.svg",
    logy=True
)
```

```python
# lp_out
# exit: 0
```