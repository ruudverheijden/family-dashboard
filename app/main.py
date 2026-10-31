"""Uvicorn entry point. Importing it does not load secrets or start background jobs."""

from .application import create_app

app = create_app()
