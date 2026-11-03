"""One board of six pairs; hidden cards stay on the server."""

import random

TITLE = "Foto-memory"
DESCRIPTION = "Zoek 6 fotoparen. Eén bord, maximaal 3 minuten."
ICON = "🃏"


def create(photos):
    cards = [p["id"] for p in photos[:6]] * 2
    random.SystemRandom().shuffle(cards)
    return {"cards": cards, "open": [], "matched": [], "moves": 0}


def play(board, value):
    if type(value) is not int or not 0 <= value < 12:
        raise ValueError
    if value in board["matched"] or value in board["open"]:
        raise ValueError
    if len(board["open"]) == 2:
        board["open"] = []
    board["open"].append(value)
    if len(board["open"]) == 2:
        board["moves"] += 1
        a, b = board["open"]
        if board["cards"][a] == board["cards"][b]:
            board["matched"].extend([a, b])
            board["open"] = []
    return len(board["matched"]) == 12


def view(board):
    visible = board["open"] + board["matched"]
    return {
        **board,
        "cards": [card if i in visible else None for i, card in enumerate(board["cards"])],
    }
