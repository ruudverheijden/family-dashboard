"""Six growing sequences with explicit feedback for the last move."""

import secrets

TITLE = "Dierenorkest"
DESCRIPTION = "Onthoud de dierenvolgorde. Haal 6 dieren, maximaal 3 minuten."
ICON = "🐸"


def create(photos):
    return {
        "sequence": [secrets.randbelow(4) for _ in range(6)],
        "round": 1,
        "input": [],
        "mistakes": 0,
        "feedback": "",
    }


def play(board, value):
    if type(value) is not int or not 0 <= value < 4:
        raise ValueError
    board["feedback"] = ""
    board["input"].append(value)
    if value != board["sequence"][len(board["input"]) - 1]:
        board["input"] = []
        board["mistakes"] += 1
        board["feedback"] = "mistake"
        return False
    if len(board["input"]) == board["round"]:
        if board["round"] == 6:
            return True
        board["round"] += 1
        board["input"] = []
    return False


def view(board):
    return {**board, "sequence": board["sequence"][: board["round"]]}
