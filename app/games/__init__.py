"""Game registry. Engines own rules; services own purchases and session lifecycle."""

from . import maze, memory, orchestra

GAMES = {"memory": memory, "orchestra": orchestra, "maze": maze}
SESSION_SECONDS = 180
