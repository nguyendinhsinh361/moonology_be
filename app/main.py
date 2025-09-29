"""
Main entry point for running the Moonology Chatbot application.

This module provides a direct way to run the application from the app directory.
"""

import uvicorn

from app import create_app
from app.core.constants import DEFAULT_HOST, DEFAULT_PORT, DEFAULT_RELOAD

# Create the app instance for direct import
app = create_app()


def run_app():
    """Run the FastAPI application with uvicorn."""
    uvicorn.run("app.main:app", host=DEFAULT_HOST, port=DEFAULT_PORT, reload=DEFAULT_RELOAD)


if __name__ == "__main__":
    run_app()
