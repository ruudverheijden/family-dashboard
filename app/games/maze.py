"""Random perfect maze: one route from mouse to cheese."""

import random

TITLE = "Doolhofavontuur"
DESCRIPTION = "Breng de muis naar de kaas. Eén doolhof, maximaal 3 minuten."
ICON = "🐭"


def create(photos):
    rng = random.SystemRandom()
    grid = [[1] * 9 for _ in range(9)]
    grid[1][1] = 0
    stack = [(1, 1)]
    while stack:
        x, y = stack[-1]
        options = [
            (x + dx, y + dy)
            for dx, dy in [(2, 0), (-2, 0), (0, 2), (0, -2)]
            if 0 < x + dx < 8 and 0 < y + dy < 8 and grid[y + dy][x + dx]
        ]
        if not options:
            stack.pop()
            continue
        nx, ny = rng.choice(options)
        grid[(y + ny) // 2][(x + nx) // 2] = grid[ny][nx] = 0
        stack.append((nx, ny))
    return {"grid": grid, "position": [1, 1], "moves": 0}


def play(board, value):
    directions = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}
    if not isinstance(value, str) or value not in directions:
        raise ValueError
    dx, dy = directions[value]
    x, y = board["position"]
    if board["grid"][y + dy][x + dx]:
        return False
    board["position"] = [x + dx, y + dy]
    board["moves"] += 1
    return board["position"] == [7, 7]


def view(board):
    return board
